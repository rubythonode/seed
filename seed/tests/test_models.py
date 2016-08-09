# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""
import datetime
import json

import mock

from django.test import TestCase, TransactionTestCase
from seed.lib.superperms.orgs.models import Organization, OrganizationUser
from seed.data_importer.models import (
    BuildingImportRecord, DataCoercionMapping, ImportFile, ImportRecord,
    TableColumnMapping
)
from seed.landing.models import SEEDUser as User
from seed import models as seed_models
from seed.mappings import mapper
from seed.tests import util
from seed.test_helpers.fake import mock_file_factory


class TestBuildingSnapshot(TestCase):
    """Test the clean methods on BuildingSnapshotModel."""

    bs1_data = {
        'pm_property_id': 1243,
        'tax_lot_id': '435/422',
        'property_name': 'Greenfield Complex',
        'custom_id_1': 1243,
        'address_line_1': '555 Database LN.',
        'address_line_2': '',
        'city': 'Gotham City',
        'postal_code': 8999,
    }
    bs2_data = {
        'pm_property_id': 9999,
        'tax_lot_id': '1231',
        'property_name': 'A Place',
        'custom_id_1': 0o000111000,
        'address_line_1': '44444 Hmmm Ave.',
        'address_line_2': 'Apt 4',
        'city': 'Gotham City',
        'postal_code': 8999,
    }

    def setUp(self):
        self.fake_user = User.objects.create(username='models_test')
        self.fake_org = Organization.objects.create()
        OrganizationUser.objects.create(
            user=self.fake_user, organization=self.fake_org
        )
        self.import_record = ImportRecord.objects.create(owner=self.fake_user)
        self.import_file1 = ImportFile.objects.create(
            import_record=self.import_record
        )
        self.import_file2 = ImportFile.objects.create(
            import_record=self.import_record
        )
        self.bs1 = util.make_fake_snapshot(
            self.import_file1,
            self.bs1_data,
            bs_type=seed_models.ASSESSED_BS,
            is_canon=True
        )
        self.bs2 = util.make_fake_snapshot(
            self.import_file2,
            self.bs2_data,
            bs_type=seed_models.PORTFOLIO_BS,
            is_canon=True
        )
        self.meter = seed_models.Meter.objects.create(
            name='test meter',
            energy_type=seed_models.ELECTRICITY,
            energy_units=seed_models.KILOWATT_HOURS
        )
        self.meter.building_snapshot.add(self.bs2)

    def _add_additional_fake_buildings(self):
        """DRY up some test code below where many BuildingSnapshots are needed."""
        self.bs3 = util.make_fake_snapshot(
            self.import_file1, self.bs1_data, bs_type=seed_models.COMPOSITE_BS,
        )
        self.bs4 = util.make_fake_snapshot(
            self.import_file1, self.bs2_data, bs_type=seed_models.COMPOSITE_BS,
        )
        self.bs5 = util.make_fake_snapshot(
            self.import_file1, self.bs2_data, bs_type=seed_models.COMPOSITE_BS,
        )

    def _test_year_month_day_equal(self, test_dt, expected_dt):
        for attr in ['year', 'month', 'day']:
            self.assertEqual(
                getattr(test_dt, attr), getattr(expected_dt, attr)
            )

    def test_clean(self):
        """Make sure we convert datestrings properly."""
        bs_model = seed_models.BuildingSnapshot()
        date_str = u'12/31/2013'

        bs_model.year_ending = date_str
        bs_model.release_date = date_str
        bs_model.generation_date = date_str

        expected_value = datetime.datetime(
            year=2013, month=12, day=31
        )

        bs_model.clean()

        self._test_year_month_day_equal(bs_model.year_ending, expected_value)
        self._test_year_month_day_equal(bs_model.release_date, expected_value)
        self._test_year_month_day_equal(
            bs_model.generation_date, expected_value
        )

    def test_source_attributions(self):
        """Test that we can point back to an attribute's source.

        This is explicitly just testing the low-level data model, none of
        the convenience functions.

        """
        bs1 = seed_models.BuildingSnapshot()
        bs1.save()

        bs1.year_ending = datetime.datetime.utcnow()
        bs1.year_ending_source = bs1
        bs1.property_name = 'Test 1234'
        bs1.property_name_source = bs1
        bs1.save()

        bs2 = seed_models.BuildingSnapshot()
        bs2.save()

        bs2.property_name = 'Not Test 1234'
        bs2.property_name_source = bs2
        bs2.year_ending = bs1.year_ending
        bs2.year_ending_source = bs1
        bs2.save()

        self.assertEqual(bs2.year_ending_source, bs1)
        self.assertEqual(bs2.property_name_source, bs2)  # We don't inherit.

    def test_create_child(self):
        """Child BS has reference to parent."""

        bs1 = seed_models.BuildingSnapshot.objects.create()
        bs2 = seed_models.BuildingSnapshot.objects.create()

        bs1.children.add(bs2)

        self.assertEqual(bs1.children.all()[0], bs2)
        self.assertEqual(bs2.parents.all()[0], bs1)
        self.assertEqual(list(bs1.parents.all()), [])
        self.assertEqual(list(bs2.children.all()), [])

    def test_get_tip(self):
        """BS tip should point to the end of the tree."""

        bs1 = seed_models.BuildingSnapshot.objects.create()
        bs2 = seed_models.BuildingSnapshot.objects.create()
        bs3 = seed_models.BuildingSnapshot.objects.create()

        bs1.children.add(bs2)
        bs2.children.add(bs3)

        self.assertEqual(bs1.tip, bs3)
        self.assertEqual(bs2.tip, bs3)
        self.assertEqual(bs3.tip, bs3)

    def test_remove_child(self):
        """Test behavior for removing a child."""
        bs1 = seed_models.BuildingSnapshot.objects.create()
        bs2 = seed_models.BuildingSnapshot.objects.create()

        bs1.children.add(bs2)

        self.assertEqual(bs1.children.all()[0], bs2)

        bs1.children.remove(bs2)

        self.assertEqual(list(bs1.children.all()), [])
        self.assertEqual(list(bs2.parents.all()), [])

    def test_get_column_mapping(self):
        """Honor organizational bounds, get mapping data."""
        org1 = Organization.objects.create()
        org2 = Organization.objects.create()

        raw_column = seed_models.Column.objects.create(
            column_name=u'Some Weird City ID',
            organization=org2
        )
        mapped_column = seed_models.Column.objects.create(
            column_name=u'custom_id_1',
            organization=org2
        )
        column_mapping1 = seed_models.ColumnMapping.objects.create(
            super_organization=org2,
        )
        column_mapping1.column_raw.add(raw_column)
        column_mapping1.column_mapped.add(mapped_column)

        # Test that it Doesn't give us a mapping from another org.
        self.assertEqual(
            seed_models.get_column_mapping(raw_column, org1, 'column_mapped'),
            None
        )

        # Correct org, but incorrect destination column.
        self.assertEqual(
            seed_models.get_column_mapping('random', org2, 'column_mapped'),
            None
        )

        # Fully correct example
        self.assertEqual(
            seed_models.get_column_mapping(
                raw_column.column_name, org2, 'column_mapped'
            ),
            (u'custom_id_1', 100)
        )

    def test_get_column_mappings(self):
        """We produce appropriate data structure for mapping"""
        expected = dict(sorted([
            (u'example_9', u'mapped_9'),
            (u'example_8', u'mapped_8'),
            (u'example_7', u'mapped_7'),
            (u'example_6', u'mapped_6'),
            (u'example_5', u'mapped_5'),
            (u'example_4', u'mapped_4'),
            (u'example_3', u'mapped_3'),
            (u'example_2', u'mapped_2'),
            (u'example_1', u'mapped_1'),
            (u'example_0', u'mapped_0')
        ]))
        org = Organization.objects.create()

        raw = []
        mapped = []
        for x in range(10):
            raw.append(seed_models.Column.objects.create(
                column_name='example_{0}'.format(x), organization=org
            ))
            mapped.append(seed_models.Column.objects.create(
                column_name='mapped_{0}'.format(x), organization=org
            ))

        for x in range(10):
            column_mapping = seed_models.ColumnMapping.objects.create(
                super_organization=org,
            )

            column_mapping.column_raw.add(raw[x])
            column_mapping.column_mapped.add(mapped[x])

        test_mapping, _ = seed_models.get_column_mappings(org)
        self.assertDictEqual(test_mapping, expected)

    def _check_save_snapshot_match_with_default(self, default_pk):
        """Test good case for saving a snapshot match."""
        self.assertEqual(seed_models.BuildingSnapshot.objects.all().count(), 2)
        bs2_canon = seed_models.CanonicalBuilding.objects.create(
            canonical_snapshot=self.bs2
        )

        self.bs2.canonical_building = bs2_canon
        self.bs2.save()

        default_building = self.bs1 if default_pk == self.bs1.pk else self.bs2

        seed_models.save_snapshot_match(
            self.bs1.pk, self.bs2.pk, confidence=0.9, user=self.fake_user, default_pk=default_pk
        )
        # We made an entirely new snapshot!
        self.assertEqual(seed_models.BuildingSnapshot.objects.all().count(), 3)
        result = seed_models.BuildingSnapshot.objects.all()[0]
        # Affirm that we give preference to the first BS passed
        # into our method.
        self.assertEqual(result.property_name, default_building.property_name)
        self.assertEqual(result.property_name_source, default_building)

        # Ensure that we transfer the meter relationship to merged children.
        self.assertEqual([r.pk for r in result.meters.all()], [self.meter.pk])

        # Test that all the parent/child relationships are sorted.
        self.assertEqual(result.confidence, 0.9)
        self.assertEqual(
            sorted([r.pk for r in result.parents.all()]),
            sorted([self.bs1.pk, self.bs2.pk])
        )

        # Test that "duplicate" CanonicalBuilding is now marked inactive.
        refreshed_bs2 = seed_models.BuildingSnapshot.objects.get(
            pk=self.bs2.pk
        )
        refreshed_bs2_canon = refreshed_bs2.canonical_building
        self.assertFalse(refreshed_bs2_canon.active)

    def test_save_snapshot_match_default_to_first_building(self):
        """Test good case for saving a snapshot match with the first building as default."""
        self._check_save_snapshot_match_with_default(self.bs1.pk)

    def test_save_snapshot_match_default_to_second_building(self):
        """Test good case for saving a snapshot match with the second building as default."""
        self._check_save_snapshot_match_with_default(self.bs2.pk)

    def test_merge_extra_data_no_data(self):
        """Test edgecase where there is no extra_data to merge."""
        test_extra, test_sources = mapper.merge_extra_data(self.bs1, self.bs2)

        self.assertDictEqual(test_extra, {})
        self.assertDictEqual(test_sources, {})

    def test_merge_extra_data(self):
        """extra_data dicts get merged proper-like."""
        self.bs1.extra_data = {'test': 'dataface', 'test2': 'nuup'}
        self.bs1.save()

        self.bs2.extra_data = {'test': 'getting overridden', 'thing': 'hi'}
        self.bs2.save()

        expected_extra = {'test': 'dataface', 'test2': 'nuup', 'thing': 'hi'}
        expected_sources = {
            'test': self.bs1.pk, 'test2': self.bs1.pk, 'thing': self.bs2.pk
        }

        test_extra, test_sources = mapper.merge_extra_data(self.bs1, self.bs2)

        self.assertDictEqual(test_extra, expected_extra)
        self.assertDictEqual(test_sources, expected_sources)

    def test_merge_extra_data_does_not_override_with_blank_data(self):
        """Test that blank fields in extra data don't override real data"""
        self.bs1.extra_data = {
            'field_a': 'data-1a',
            'field_b': '',
            'field_c': '',
        }
        self.bs1.save()

        self.bs2.extra_data = {
            'field_a': 'data-2a',
            'field_b': 'data-2b',
            'field_c': '',
        }
        self.bs2.save()

        expected_extra = {
            'field_a': 'data-1a',
            'field_b': 'data-2b',
            'field_c': '',
        }
        expected_sources = {
            'field_a': self.bs1.pk,
            'field_b': self.bs2.pk,
            'field_c': self.bs1.pk,
        }

        actual_extra, actual_sources = mapper.merge_extra_data(self.bs1, self.bs2)

        self.assertDictEqual(actual_extra, expected_extra)
        self.assertDictEqual(actual_sources, expected_sources)

    def test_update_building(self):
        """Good case for updating a building."""
        fake_building_extra = {
            u'Assessor Data 1': u'2342342',
            u'Assessor Data 2': u'245646',
        }
        fake_building_kwargs = {
            u'property_name': u'Place pl.',
            u'address_line_1': u'332 Place pl.',
            u'owner': u'Duke of Earl',
            u'postal_code': u'68674',
        }

        fake_building = util.make_fake_snapshot(
            self.import_file2,
            fake_building_kwargs,
            seed_models.COMPOSITE_BS,
            is_canon=True
        )

        fake_building.super_organization = self.fake_org
        fake_building.extra_data = fake_building_extra
        fake_building.save()

        # add building to a project
        project = seed_models.Project.objects.create(
            name='test project',
            owner=self.fake_user,
            super_organization=self.fake_org,
        )
        seed_models.ProjectBuilding.objects.create(
            building_snapshot=fake_building,
            project=project
        )

        fake_building_pk = fake_building.pk
        fake_building = seed_models.BuildingSnapshot.objects.filter(pk=fake_building_pk).first()

        fake_building_kwargs[u'property_name_source'] = fake_building.pk
        fake_building_kwargs[u'address_line_1_source'] = fake_building.pk
        fake_building_kwargs[u'owner_source'] = fake_building.pk
        seed_models.set_initial_sources(fake_building)

        # Hydrated JS version will have this, we'll query off it.
        fake_building_kwargs[u'pk'] = fake_building.pk
        # "update" one of the field values.
        fake_building_kwargs[u'import_file'] = self.import_file1
        fake_building_kwargs[u'postal_code'] = u'99999'
        fake_building_extra[u'Assessor Data 1'] = u'NUP.'
        # Need to simulate JS hydrated payload here.
        fake_building_kwargs[u'extra_data'] = fake_building_extra

        new_snap = seed_models.update_building(
            fake_building, fake_building_kwargs, self.fake_user
        )

        # Make sure new building is also in project.
        pbs = seed_models.ProjectBuilding.objects.filter(
            building_snapshot=new_snap,
        )
        self.assertEqual(pbs.count(), 1)

        # Make sure our value was updated.
        self.assertEqual(
            new_snap.postal_code, fake_building_kwargs[u'postal_code']
        )

        self.assertNotEqual(new_snap.pk, fake_building.pk)

        # Make sure that the extra data were saved, with orig sources.
        self.assertDictEqual(
            new_snap.extra_data, fake_building_extra
        )

        # Make sure we have the same orgs.
        self.assertEqual(
            new_snap.super_organization, fake_building.super_organization
        )

        self.assertEqual(new_snap.match_type, fake_building.match_type)
        # Make sure we're set as the source for updated info!!!
        self.assertEqual(new_snap, new_snap.postal_code_source)
        # Make sure our sources from parent get set properly.
        for attr in ['property_name', 'address_line_1', 'owner']:
            self.assertEqual(
                getattr(new_snap, '{0}_source'.format(attr)).pk,
                fake_building.pk
            )
        # Make sure our parent is set.
        self.assertEqual(new_snap.parents.all()[0].pk, fake_building.pk)

        # Make sure we captured all of the extra_data column names after update
        data_columns = seed_models.Column.objects.filter(
            organization=fake_building.super_organization,
            is_extra_data=True
        )

        self.assertEqual(data_columns.count(), len(fake_building_extra))
        self.assertListEqual(
            sorted([d.column_name for d in data_columns]),
            sorted(fake_building_extra.keys())
        )

    def test_update_building_with_dates(self):
        fake_building_kwargs = {
            u'extra_data': {}
        }

        fake_building = util.make_fake_snapshot(
            self.import_file2,
            fake_building_kwargs,
            seed_models.COMPOSITE_BS,
            is_canon=True
        )

        fake_building.super_organization = self.fake_org
        fake_building.save()

        fake_building_pk = fake_building.pk
        fake_building = seed_models.BuildingSnapshot.objects.filter(pk=fake_building_pk).first()

        fake_building_kwargs['year_ending'] = '12/30/2015'

        new_snap = seed_models.update_building(
            fake_building, fake_building_kwargs, self.fake_user
        )

        self.assertNotEqual(new_snap.pk, fake_building.pk)

    def test_recurse_tree(self):
        """Make sure we get an accurate child tree."""
        self._add_additional_fake_buildings()
        can = self.bs1.canonical_building
        # Make our child relationships.
        self.bs1.children.add(self.bs3)
        self.bs3.children.add(self.bs4)
        self.bs4.children.add(self.bs5)

        can.canonical_snapshot = self.bs5
        can.save()

        child_expected = [self.bs3, self.bs4, self.bs5]
        # Here we're actually testing ``child_tree`` property
        self.assertEqual(self.bs1.child_tree, child_expected)

        # Leaf node condition.
        self.assertEqual(self.bs5.child_tree, [])

        # And here ``parent_tree`` property
        parent_expected = [self.bs1, self.bs3, self.bs4]
        self.assertEqual(self.bs5.parent_tree, parent_expected)

        # Root parent case
        self.assertEqual(self.bs1.parent_tree, [])

    def test_unmatch_snapshot_tree_last_match(self):
        """
        Tests the simplest case of unmatching a building where the child
        snapshot created from the original matching has not since been
        matched with another building (no children).
        """
        self._add_additional_fake_buildings()

        # simulate matching bs1 and bs2 to have a child of bs3
        self.bs1.children.add(self.bs3)
        self.bs2.children.add(self.bs3)

        canon = self.bs1.canonical_building
        canon2 = self.bs2.canonical_building
        canon2.active = False
        canon2.save()

        self.bs3.canonical_building = canon
        self.bs3.save()
        canon.canonical_snapshot = self.bs3
        canon.save()

        # unmatch bs2 from bs1
        seed_models.unmatch_snapshot_tree(self.bs2.pk)

        canon = seed_models.CanonicalBuilding.objects.get(pk=canon.pk)
        canon2 = seed_models.CanonicalBuilding.objects.get(pk=canon2.pk)
        bs1 = seed_models.BuildingSnapshot.objects.get(pk=self.bs1.pk)
        # bs2 = seed_models.BuildingSnapshot.objects.get(pk=self.bs2.pk)

        self.assertEqual(canon.canonical_snapshot, bs1)
        self.assertEqual(bs1.children.count(), 0)
        self.assertEqual(canon2.active, True)

    def test_unmatch_snapshot_tree_prior_match(self):
        """
        Tests the more complicated case of unmatching a building after
        more buildings have been matched to the snapshot resulting from
        the original match.
        """
        self._add_additional_fake_buildings()

        # simulate matching bs1 and bs2 to have a child of bs3
        self.bs1.children.add(self.bs3)
        self.bs2.children.add(self.bs3)

        canon = self.bs1.canonical_building
        canon2 = self.bs2.canonical_building
        canon2.active = False
        canon2.save()

        self.bs3.canonical_building = canon
        self.bs3.save()
        canon.canonical_snapshot = self.bs3
        canon.save()

        # now simulate matching bs4 and bs3 to have a child of bs5
        self.bs3.children.add(self.bs5)
        self.bs4.children.add(self.bs5)

        self.bs5.canonical_building = canon
        self.bs5.save()
        canon.canonical_snapshot = self.bs5
        canon.save()

        # simulating the following tree:
        # b1 b2
        # \ /
        #  b3 b4
        #  \ /
        #   b5

        # unmatch bs2 from bs1
        seed_models.unmatch_snapshot_tree(self.bs2.pk)

        canon = seed_models.CanonicalBuilding.objects.get(pk=canon.pk)
        canon2 = seed_models.CanonicalBuilding.objects.get(pk=canon2.pk)

        # bs3, and bs5 should be deleted
        deleted_pks = [self.bs3.pk, self.bs5.pk]
        bs_manager = seed_models.BuildingSnapshot.objects
        theoretically_empty_set = bs_manager.filter(pk__in=deleted_pks)

        self.assertEqual(theoretically_empty_set.count(), 0)

        bs2 = bs_manager.get(pk=self.bs2.pk)
        self.assertEqual(bs2.has_children, False)
        self.assertEqual(canon2.active, True)

    def test_unmatch_snapshot_tree_retains_canonical_snapshot(self):
        """
        TODO:
        """
        self.bs3 = util.make_fake_snapshot(
            self.import_file1, self.bs1_data, bs_type=seed_models.COMPOSITE_BS,
            is_canon=True,
        )
        self.bs4 = util.make_fake_snapshot(
            self.import_file1, self.bs2_data, bs_type=seed_models.COMPOSITE_BS,
            is_canon=True,
        )

        # simulate matching bs1 and bs2 to have a child of bs3
        seed_models.save_snapshot_match(self.bs2.pk, self.bs1.tip.pk)
        seed_models.save_snapshot_match(self.bs3.pk, self.bs1.tip.pk)
        seed_models.save_snapshot_match(self.bs4.pk, self.bs1.tip.pk)

        tip_pk = self.bs1.tip.pk

        # simulating the following tree:
        # b1 b2
        # \ /
        #  b3 b4
        #  \ /
        #   b5

        # unmatch bs3 from bs4
        seed_models.unmatch_snapshot_tree(self.bs4.pk)

        # tip should be deleted
        self.assertFalse(seed_models.BuildingSnapshot.objects.filter(pk=tip_pk).exists())

        canon_bs4 = seed_models.CanonicalBuilding.objects.get(pk=self.bs4.canonical_building_id)

        # both of their canons should be active
        self.assertTrue(canon_bs4.active)

        # both cannons should have a canonical_snapshot
        self.assertEqual(canon_bs4.canonical_snapshot, self.bs4)


class TestCanonicalBuilding(TestCase):
    """Test the clean methods on CanonicalBuildingModel."""

    def test_repr(self):
        c = seed_models.CanonicalBuilding()
        c.save()
        self.assertTrue('pk: %s' % c.pk in str(c))
        self.assertTrue('snapshot: None' in str(c))
        self.assertTrue('- active: True' in str(c))

        c.active = False
        c.save()
        self.assertTrue('- active: False' in str(c))

        b = seed_models.BuildingSnapshot()
        b.save()
        c.canonical_snapshot = b
        c.save()
        self.assertTrue('snapshot: %s' % b.pk in str(c))
        self.assertEqual(
            'pk: %s - snapshot: %s - active: False' % (c.pk, b.pk),
            str(c)
        )


class TestColumnMapping(TestCase):
    """Test ColumnMapping utility methods."""

    def setUp(self):

        foo_col = seed_models.Column.objects.create(column_name="foo")
        bar_col = seed_models.Column.objects.create(column_name="bar")
        baz_col = seed_models.Column.objects.create(column_name="baz")

        dm = seed_models.ColumnMapping.objects.create()
        dm.column_raw.add(foo_col)
        dm.column_mapped.add(baz_col)

        cm = seed_models.ColumnMapping.objects.create()
        cm.column_raw.add(foo_col, bar_col)
        cm.column_mapped.add(baz_col)

        self.directMapping = dm
        self.concatenatedMapping = cm

    def test_is_direct(self):
        self.assertEqual(self.directMapping.is_direct(), True)
        self.assertEqual(self.concatenatedMapping.is_direct(), False)

    def test_is_concatenated(self):
        self.assertEqual(self.directMapping.is_concatenated(), False)
        self.assertEqual(self.concatenatedMapping.is_concatenated(), True)


class TestImportRecord(TestCase):
    """Test ImportRecord methods and properties"""
    def setUp(self):
        self.import_record = ImportRecord.objects.create()

    def tearDown(self):
        ImportFile.objects.all().delete()
        BuildingImportRecord.objects.all().delete()
        self.import_record.delete()

    def test_num_files(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_files, 3)

    # test fails - method refers to non existent key initial_mapping_done
    def test_num_files_mapped(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_files_mapped, 3)

    # test fails - method refers to non existent key initial_mapping_done
    def test_num_files_to_map(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_files_to_map, 3)

    # test fails - method refers to non existent key initial_mapping_done
    def test_percent_files_mapped(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.percent_files_mapped, 100)

    # test fails - method refers to non existent key coercion_mapping_done
    def test_num_files_cleaned(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_files_cleaned, 3)

    # test fails - method refers to non existent key coercion_mapping_done
    def test_num_files_to_clean(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_files_to_clean, 3)

    # test fails - method refers to non existent key coercion_mapping_done
    def test_percent_files_cleaned(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.percent_files_cleaned, 100)

    # passes but unused
    def test_num_files_merged(self):
        self.import_record._num_ready_for_import = 0
        self.assertEqual(self.import_record.num_files_merged, 0)

    # passes but unused
    def test_num_files_to_merge(self):
        self.import_record._num_ready_for_import = 0
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_files_to_merge, 3)

    # passes but unused
    def test_percent_files_ready_to_merge(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.percent_files_ready_to_merge, 100)

    # passes but unused
    def test_num_ready_for_import(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_ready_for_import, 3)

    # passes but unused
    def test_num_not_ready_for_import(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_not_ready_for_import, 0)

    # passes but unused
    def test_ready_for_import(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertTrue(self.import_record.ready_for_import)

    # passes but unused
    def test_percent_ready_for_import(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1,
            num_tasks_total=1, num_tasks_complete=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2,
            num_tasks_total=1, num_tasks_complete=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3,
            num_tasks_total=1, num_tasks_complete=1
        )
        self.assertEqual(self.import_record.percent_ready_for_import, 100)

    # passes but unused
    def test_percent_ready_for_import_by_file_count(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(
            self.import_record.percent_ready_for_import_by_file_count, 100
        )

    # passes but unused
    def test_num_failed_tablecolumnmappings(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_failed_tablecolumnmappings, 0)

    # passes but unused except in initial migration
    def test_num_coercion_errors(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_coercion_errors, 0)

    # fails as import_file.num_validation_errors may be None
    # coercion_errors sets default to 1 but not validation error
    def test_num_validation_errors(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_validation_errors, 0)
        f4 = mock_file_factory('file4.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f4, num_validation_errors=1
        )
        self.assertEqual(self.import_record.num_validation_errors, 1)

    # fails as import_file.num_rows may be None, appears unused
    def test_num_rows(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        f1 = mock_file_factory('file1.csv')
        self.assertEqual(self.import_record.num_rows, 0)

    def test_num_rows_import_file_has_num_rows(self):
        f1 = mock_file_factory('file1.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_rows=1
        )
        self.assertEqual(self.import_record.num_rows, 1)

    # fails as import_file.num_columns may be None, appears unused
    def test_num_columns(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.num_columns, 0)

    def test_num_columns_import_file_has_num_columns(self):
        f1 = mock_file_factory('file1.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1
        )
        self.assertEqual(self.import_record.num_columns, 1)

    # fails as import_file.file_size_in_bytes may be None, appears unused
    def test_total_file_size(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.total_file_size, 0)

    def test_total_file_size_import_file_has_file_size(self):
        f1 = mock_file_factory('file1.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, file_size_in_bytes=1000
        )
        self.assertEqual(self.import_record.total_file_size, 1000)

    # fails as import_file.num_validation_errors etc may be None, appears unused
    def test_total_correct_mappings(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.total_correct_mappings, 0)

    def test_total_correct_mappings_ready_for_import_is_100(self):
        self.import_record._percent_ready_for_import = 100
        self.assertEqual(self.import_record.total_correct_mappings, 100)

    def test_total_correct_mappings_attributes_set(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1,
            num_validation_errors=1, num_coercion_errors=0,
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2,
            num_validation_errors=0, num_coercion_errors=1,
        )
        ifl = ImportFile.objects.create(
            import_record=self.import_record, file=f3,
            num_validation_errors=0, num_coercion_errors=0,
        )
        TableColumnMapping.objects.create(source_string='test', import_file=ifl)
        self.import_record._percent_ready_for_import = 0
        self.assertEqual(self.import_record.total_correct_mappings, 3)

    # appears unused except internally by pct_merge_complete
    def test_merge_progress_key(self):
        self.assertEqual(
            self.import_record.merge_progress_key,
            "merge_progress_pct_" + str(self.import_record.pk)
        )

    # appears unused
    def test_match_progress_key(self):
        self.assertEqual(
            self.import_record.match_progress_key,
            "match_progress_pct_" + str(self.import_record.pk)
        )

    # appears unused
    def test_merge_status_key(self):
        self.assertEqual(
            self.import_record.merge_status_key,
            "merge_import_record_status_" + str(self.import_record.pk)
        )

    # appears unused
    @mock.patch('seed.data_importer.models.get_cache')
    def test_pct_merge_complete(self, mock_get_cache):
        mock_get_cache.return_value = {'progress': 100}
        self.assertEqual(
            self.import_record.pct_merge_complete,
            100
        )
        mock_get_cache.assert_called_with(
            "merge_progress_pct_" + str(self.import_record.pk)
        )

    # appears unused
    def test_premerge_seconds_remaining_key(self):
        self.assertEqual(
            self.import_record.premerge_seconds_remaining_key,
            "premerge_seconds_remaining_" + str(self.import_record.pk)
        )

    # appears unused
    def test_MAPPING_ACTIVE_KEY(self):
        self.assertEqual(
            self.import_record.MAPPING_ACTIVE_KEY,
            "IR_MAPPING_ACTIVE" + str(self.import_record.pk)
        )

    # appears unused
    def test_MAPPING_QUEUED_KEY(self):
        self.assertEqual(
            self.import_record.MAPPING_QUEUED_KEY,
            "IR_MAPPING_QUEUED" + str(self.import_record.pk)
        )

    # appears unused
    @mock.patch('seed.data_importer.models.get_cache_raw')
    def test_estimated_seconds_remaining(self, mock_get_cache_raw):
        mock_get_cache_raw.return_value = 100
        self.assertEqual(
            self.import_record.estimated_seconds_remaining,
            100
        )
        mock_get_cache_raw.assert_called_with(
            "merge_seconds_remaining_" + str(self.import_record.pk)
        )

    # appears unused
    @mock.patch('seed.data_importer.models.get_cache')
    def test_merge_status(self, mock_get_cache):
        mock_get_cache.return_value = {'status': 'test'}
        self.assertEqual(
            self.import_record.merge_status,
            'test'
        )
        mock_get_cache.assert_called_with(
            "merge_import_record_status_" + str(self.import_record.pk)
        )

    # appears unused
    @mock.patch('seed.data_importer.models.get_cache_raw')
    def test_estimated_premerge_seconds_remaining(self, mock_get_cache_raw):
        mock_get_cache_raw.return_value = 100
        self.assertEqual(
            self.import_record.premerge_estimated_seconds_remaining,
            100
        )
        mock_get_cache_raw.assert_called_with(
            "premerge_seconds_remaining_" + str(self.import_record.pk)
        )

    def test_matched_buildings(self):
        bir = BuildingImportRecord.objects.create(
            import_record=self.import_record,
            was_in_database=True
        )
        result = self.import_record.matched_buildings
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pk, bir.pk)

    def test_num_matched_buildings(self):
        BuildingImportRecord.objects.create(
            import_record=self.import_record,
            was_in_database=True
        )
        result = self.import_record.num_matched_buildings
        self.assertEqual(result, 1)

    def test_new_buildings(self):
        bir = BuildingImportRecord.objects.create(
            import_record=self.import_record,
            was_in_database=False,
            is_missing_from_import=False
        )
        result = self.import_record.new_buildings
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pk, bir.pk)

    def test_num_new_buildings(self):
        BuildingImportRecord.objects.create(
            import_record=self.import_record,
            was_in_database=False,
            is_missing_from_import=False
        )
        result = self.import_record.num_new_buildings
        self.assertEqual(result, 1)

    def test_missing_buildings(self):
        bir = BuildingImportRecord.objects.create(
            import_record=self.import_record,
            is_missing_from_import=True
        )
        result = self.import_record.missing_buildings
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].pk, bir.pk)

    def test_num_missing_buildings(self):
        BuildingImportRecord.objects.create(
            import_record=self.import_record,
            is_missing_from_import=True
        )
        result = self.import_record.num_missing_buildings
        self.assertEqual(result, 1)

    def test_num_buildings_imported_total(self):
        BuildingImportRecord.objects.create(
            import_record=self.import_record,
            was_in_database=True
        )
        BuildingImportRecord.objects.create(
            import_record=self.import_record,
            was_in_database=False,
            is_missing_from_import=False
        )
        BuildingImportRecord.objects.create(
            import_record=self.import_record,
            is_missing_from_import=True
        )
        result = self.import_record.num_buildings_imported_total
        self.assertEqual(result, 3)

    # Fails: references non-existant key (coercion_mapping_done) on ImportFile
    def test_status_percent_STATUS_MACHINE_CLEANING(self):
        self.import_record.status = 3
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3, num_columns=1, num_rows=1
        )
        self.assertEqual(self.import_record.status_percent, 100.0)

    # Fails: references non-existant key (coercion_mapping_done) on ImportFile
    def test_status_percent_STATUS_CLEANING(self):
        self.import_record.status = 4
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3, num_columns=1, num_rows=1
        )
        self.assertEqual(self.import_record.status_percent, 100.0)

    # Fails: references non-existant key (coercion_mapping_done) on ImportFile
    def test_status_percent_STATUS_MAPPING(self):
        self.import_record.status = 4
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3, num_columns=1, num_rows=1
        )
        self.assertEqual(self.import_record.status_percent, 100.0)

    @mock.patch('seed.data_importer.models.get_cache')
    def test_status_percent_premerge_analysis_active(self, mock_get_cache):
        mock_get_cache.return_value = {'progress': 70.0}
        self.import_record.premerge_analysis_active = True
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3, num_columns=1, num_rows=1
        )
        self.assertEqual(self.import_record.status_percent, 70.0)

    @mock.patch('seed.data_importer.models.get_cache')
    def test_status_percent_merge_analysis_active(self, mock_get_cache):
        mock_get_cache.return_value = {'progress': 70.0}
        self.import_record.merge_analysis_active = True
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3, num_columns=1, num_rows=1
        )
        self.assertEqual(self.import_record.status_percent, 70.0)

    def test_status_percent_is_imported_live(self):
        self.import_record.is_imported_live = True
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(
            import_record=self.import_record, file=f1, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f2, num_columns=1, num_rows=1
        )
        ImportFile.objects.create(
            import_record=self.import_record, file=f3, num_columns=1, num_rows=1
        )
        self.assertEqual(self.import_record.status_percent, 100.0)

    # test fails - reference to non existent key coercion_mapping_done on ImportFile
    def test_status_numerator_STATUS_CLEANING(self):
        self.import_record.status = 4
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.status_numerator, 3)

    # test fails - reference to non existent key coercion_mapping_done on ImportFile
    def test_status_numerator_STATUS_MAPPING(self):
        self.import_record.status = 2
        self.import_record.save()
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.status_numerator, 3)

    # only refered to in broken methods
    def test_status_denominator(self):
        f1 = mock_file_factory('file1.csv')
        f2 = mock_file_factory('file2.csv')
        f3 = mock_file_factory('file3.csv')
        ImportFile.objects.create(import_record=self.import_record, file=f1)
        ImportFile.objects.create(import_record=self.import_record, file=f2)
        ImportFile.objects.create(import_record=self.import_record, file=f3)
        self.assertEqual(self.import_record.status_denominator, 3)

    def test_urls(self):
        # not required? is bpd still a thing?
        self.assertEqual(self.import_record.app_namespace, 'seed')
        # don't work, no reverse
        # self.import_record.pre_merge_url
        # self.import_record.worksheet_url
        # self.import_record.add_files_url
        # self.import_record.premerge_progress_url
        # self.import_record.start_merge_url
        # self.import_record.merge_url
        # self.import_record.dashboard_url
        # self.import_record.search_url
        # self.import_record.delete_url
        # self.import_record.save_import_meta_url

        # refers to above
        # self.import_record.status_url

    def test_mark_merged(self):
        then = datetime.datetime.now()
        self.import_record.mark_merged()
        now = datetime.datetime.now()
        self.assertTrue(self.import_record.merge_analysis_done)
        self.assertFalse(self.import_record.merge_analysis_active)
        self.assertTrue(self.import_record.is_imported_live)
        assert then <= self.import_record.import_completed_at <= now

    def test_mark_merge_started(self):
        self.import_record.mark_merge_started()
        self.assertFalse(self.import_record.merge_analysis_done)
        self.assertTrue(self.import_record.merge_analysis_active)
        self.assertFalse(self.import_record.merge_analysis_queued)

    # fails with Type Error: can't subtract offset-naive and offset-aware datetimes
    # references non existent keys
    def test_to_json(self):
        updated_at = datetime.datetime.now() - datetime.timedelta(minutes=1)
        self.import_record.updated_at = updated_at
        self.import_record.save()
        assert False
        # self.import_record.to_json

    # Fails dues to failed reverse etc
    @mock.patch('seed.data_importer.models.get_cache_state')
    def test_worksheet_progress_json(self, mock_get_cache_state):
        mock_get_cache_state.return_value = True
        self.assertNotEqual(self.import_record.worksheet_progress_json, [])


class TestImportFile(TransactionTestCase):
    """Test ImportRecord methods and properties"""

    def setUp(self):
        mock_csv_patch = mock.patch(
            'seed.data_importer.models.csv.reader',
        )
        self.addCleanup(mock_csv_patch.stop)
        self.mock_csv_reader = mock_csv_patch.start()
        self.mock_csv_reader.return_value = [['a', 'b', 'c'], ['d', 'e', 'f']]
        self.import_record = ImportRecord.objects.create()
        self.file = mock_file_factory('file1.csv')
        self.import_file = ImportFile.objects.create(
            import_record=self.import_record, file=self.file
        )

    def tearDown(self):
        ImportFile.objects.all().delete()
        ImportRecord.objects.all().delete()
        TableColumnMapping.objects.all().delete()
        DataCoercionMapping.objects.all().delete()

    # appears unused
    def test_data_rows(self):
        result = [i for i in self.import_file.data_rows]
        self.assertEqual(result, [['a', 'b', 'c'], ['d', 'e', 'f']])

    # appears unused
    def test_cleaned_data_rows(self):
        tcm = TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1
        )
        DataCoercionMapping.objects.create(
            table_column_mapping=tcm, source_string='a', source_type='test',
            destination_value='x'
        )
        result = [i for i in self.import_file.cleaned_data_rows]
        # note removes columns with no tablecolumnmapping
        self.assertEqual(result, [['x'], ['d']])

    # unused, contains faulty assumptions according to seed/tasks.py L 705
    def test_cache_first_rows(self):
        self.import_file.cache_first_rows()
        self.assertEqual(self.import_file.cached_first_row, 'a|#*#|b|#*#|c')
        self.assertEqual(
            self.import_file.cached_second_to_fifth_row, 'd|#*#|e|#*#|f\n'
        )
        self.assertEqual(self.import_file.num_rows, 1)
        self.assertEqual(self.import_file.num_columns, 3)

    # appears unused
    # only works if cache_first_rows() is called first, but does not check
    def test_second_to_fifth_rows(self):
        self.import_file.cache_first_rows()
        self.assertEqual(
            self.import_file.second_to_fifth_rows, [['d', 'e', 'f']]
        )

    # only used in broken method
    def test_num_mapping_total(self):
        self.assertEqual(self.import_file.num_mapping_total, 0)
        TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1
        )
        self.assertEqual(self.import_file.num_mapping_total, 1)

    # appears unused
    def test_num_mapping_remaining(self):
        # method contains useless use of ||
        self.assertEqual(self.import_file.num_mapping_errors, 0)
        self.assertEqual(self.import_file.num_mapping_remaining, 0)

    # appears unused
    def test_num_mapping_complete(self):
        # method contains useless use of ||
        self.assertEqual(self.import_file.num_mapping_complete, 0)
        TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1
        )
        self.assertEqual(self.import_file.num_mapping_complete, 1)

    # appears unused
    def test_num_cleaning_complete(self):
        self.assertEqual(self.import_file.num_cleaning_complete, 0)

    # appears unused
    # only works if cache_first_rows() is called first, but does not check
    def test_num_cells(self):
        self.import_file.cache_first_rows()
        self.assertEqual(self.import_file.num_cells, 3)

    # appears unused
    # only works if cache_first_rows() is called first, but does not check
    def test_tcm_json(self):
        TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1
        )
        self.import_file.cache_first_rows()
        results = json.loads(self.import_file.tcm_json)
        self.assertEqual(results[0]["header_row"], 'a')
        self.assertEqual(results[0]["order"], 1)

    # appears unused
    def test_tcm_errors_json(self):
        self.assertEqual(self.import_file.tcm_json, '[]')
        # only works if cache_first_rows() is called first, but does not check
        TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1,
            error_message_text='test\n'
        )
        self.import_file.cache_first_rows()
        results = json.loads(self.import_file.tcm_errors_json)
        self.assertEqual(results[0]["order"], 1)
        self.assertEqual(results[0]["error_message_text"], '')
        TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=2,
            error_message_text='test\n', destination_model='test',
            destination_field='test'
        )
        results = json.loads(self.import_file.tcm_errors_json)
        self.assertEqual(results[1]["order"], 2)
        self.assertEqual(results[1]["error_message_text"], 'test<br/>')

    # appears unused
    @mock.patch('seed.data_importer.models.delete_cache')
    @mock.patch('seed.data_importer.models.set_cache_state')
    @mock.patch('seed.data_importer.models.get_cache_state')
    @mock.patch('seed.data_importer.models.get_cache_raw')
    def test_update_tcms_from_save(self, mock_get_cache_raw, mock_get_cache_state,
                                   mock_set_cache_state, mock_delete_cache):
        mock_get_cache_raw.side_effect = [1, True, '{}', 2, None, False]
        mock_get_cache_state.side_effect = [False, False]

        tcm = TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1
        )
        self.assertFalse(tcm.was_a_human_decision)

        queued_tcm_save = "QUEUED_TCM_SAVE_{}".format(tcm.pk)
        queued_tcm_data_key = "QUEUED_TCM_DATA_KEY{}".format(tcm.pk)
        updating_tcms_key = "UPDATING_TCMS_KEY{}".format(tcm.pk)

        json_data = json.dumps(
            [{'pk': tcm.pk, 'destination_model': 'test',
             'destination_field': 'test', 'ignored': False}]
        )

        result = self.import_file.update_tcms_from_save(json_data, 2)
        tcm = TableColumnMapping.objects.get(pk=tcm.pk)

        self.assertTrue(result)
        self.assertTrue(tcm.was_a_human_decision)

        self.assertEqual(
            mock_get_cache_raw.call_args_list,
            [
                mock.call(queued_tcm_save, None),
                mock.call(queued_tcm_save, False),
                mock.call(queued_tcm_data_key),
                mock.call(queued_tcm_save),
                mock.call(queued_tcm_save, None),
                mock.call(queued_tcm_save, False),
            ]
        )

        self.assertEqual(
            mock_get_cache_state.call_args_list,
            [
                mock.call(updating_tcms_key, None),
                mock.call(updating_tcms_key, None)
            ]
        )

        self.assertEqual(
            mock_set_cache_state.call_args_list,
            [
                mock.call(updating_tcms_key, True),
                mock.call(updating_tcms_key, True)
            ]
        )

        self.assertEqual(
            mock_delete_cache.call_args_list,
            [
                mock.call(queued_tcm_data_key),
                mock.call(queued_tcm_save),
                mock.call(updating_tcms_key),
                mock.call(updating_tcms_key),
                mock.call(queued_tcm_data_key),
                mock.call(queued_tcm_save),
                mock.call(updating_tcms_key),
                mock.call(queued_tcm_data_key),
                mock.call(queued_tcm_save),
            ]
        )

    @mock.patch('seed.data_importer.models.set_cache_raw')
    @mock.patch('seed.data_importer.models.get_cache_state')
    @mock.patch('seed.data_importer.models.get_cache_raw')
    def test_update_tcms_from_save_false(
            self, mock_get_cache_raw, mock_get_cache_state, mock_set_cache_raw):
        mock_get_cache_raw.return_value = 1
        mock_get_cache_state.return_value = True

        tcm = TableColumnMapping.objects.create(
            import_file=self.import_file, source_string='test', order=1
        )
        self.assertFalse(tcm.was_a_human_decision)

        queued_tcm_save = "QUEUED_TCM_SAVE_{}".format(tcm.pk)
        queued_tcm_data_key = "QUEUED_TCM_DATA_KEY{}".format(tcm.pk)
        updating_tcms_key = "UPDATING_TCMS_KEY{}".format(tcm.pk)

        json_data = json.dumps(
            [{'pk': tcm.pk, 'destination_model': 'test',
             'destination_field': 'test', 'ignored': False}]
        )

        result = self.import_file.update_tcms_from_save(json_data, 2)
        tcm = TableColumnMapping.objects.get(pk=tcm.pk)

        self.assertFalse(result)
        self.assertFalse(tcm.was_a_human_decision)
        self.assertEqual(
            mock_get_cache_raw.call_args,
            mock.call(queued_tcm_save, None)
        )
        self.assertEqual(
            mock_get_cache_state.call_args,
            mock.call(updating_tcms_key, None)
        )
        self.assertEqual(
            mock_set_cache_raw.call_args_list,
            [
                mock.call(queued_tcm_save, 2),
                mock.call(queued_tcm_data_key, json_data)
            ]
        )

    # will fail, references non-existent property  coercion_mapping_done
    @mock.patch('seed.data_importer.models.get_cache_state')
    @mock.patch('seed.data_importer.models.get_cache')
    def test_cleaning_progress_pct(self, mock_get_cache, mock_get_cache_state):
        mock_get_cache_state.side_effect = (
            False, False, True, False, False, True, False, False
        )
        # not self.coercion_mapping_active and not self.coercion_mapping_queued
        # and self.num_coercions_total > 0
        mock_get_cache.return_value = {'progress': 50.0}
        self.import_file.num_coercions_total = 1
        self.assertEqual(self.import_file.cleaning_progress_pct, 100.0)

        self.import_file.num_coercions_total = 0

        # coercion_mapping_active = True
        self.assertEqual(self.import_file.cleaning_progress_pct, 50.0)

        # below will fail, references non-existent property  coercion_mapping_done
        # i.e self.import_file.coercion_mapping_done = False

        # coercion_mapping_active = False, coercion_mapping_queued = True
        self.assertEqual(self.import_file.cleaning_progress_pct, 0.0)

        # coercion_mapping_active = False, coercion_mapping_queued = False
        # coercion_mapping_done = False
        self.assertEqual(self.import_file.cleaning_progress_pct, 0.0)

        # coercion_mapping_active = False, coercion_mapping_queued = False
        # coercion_mapping_done = True
        self.assertEqual(self.import_file.cleaning_progress_pct, 100.0)

    @mock.patch('seed.data_importer.models.get_cache_state')
    def test_export_ready(self, mock_get_cache_state):
        mock_get_cache_state.side_effect = (True, False, True, True)

        export_file = mock_file_factory('export_file.csv')
        self.import_file.export_file = export_file
        self.assertTrue(self.import_file.export_ready)

        # get_cache_state(self.EXPORT_READY_CACHE_KEY, True) = False
        self.assertFalse(self.import_file.export_ready)

        # fails as self.export_file is None is not true if export_file
        # is null should be == None (FileField overides __eq__)
        # get_cache_state(self.EXPORT_READY_CACHE_KEY, True) = True
        self.import_file.export_file = None
        self.assertFalse(self.import_file.export_ready)

        # get_cache_state(self.EXPORT_READY_CACHE_KEY, True) = True
        self.import_file.export_file = ''
        self.assertFalse(self.import_file.export_ready)

    # fails as no reverse for url
    def test_urls(self):
        self.assertNotEqual(
            self.import_file.export_url, None
        )
        self.assertNotEqual(
            self.import_file.generate_url, None
        )
        self.assertNotEqual(
            self.import_file._merge_progress_url, None
        )
        self.assertNotEqual(
            self.import_file.premerge_progress_url, None
        )
        self.assertNotEqual(
            self.import_file.restart_cleaning_url, None
        )


class TestTableColumnMapping(TestCase):

    def setUp(self):
        self.import_record = ImportRecord.objects.create()
        self.file = mock_file_factory('file1.csv')
        self.import_file = ImportFile.objects.create(
            import_record=self.import_record, file=self.file
        )
        self.tcm = TableColumnMapping.objects.create(
            source_string='test', import_file=self.import_file,
            destination_model='TestModel', destination_field='test_field'
        )

    def tearDown(self):
        ImportFile.objects.all().delete()
        ImportRecord.objects.all().delete()
        TableColumnMapping.objects.all().delete()

    @mock.patch('seed.data_importer.models.hashlib')
    def test_source_string_sha(self, mock_hashlib):
        mock_hashlib.md5.return_value.hexdigest.return_value = '012345ab'
        self.assertEqual(self.tcm.source_string_sha, '012345ab')
        mock_hashlib.md5.assert_called()
        mock_hashlib.md5.return_value.update.assert_called_with('test')

    def test_string_properties(self):
        self.assertEqual(self.tcm.combined_model_and_field, 'TestModel.test_field')
        self.assertEqual(self.tcm.friendly_destination_model, 'Test Model')
        self.assertEqual(self.tcm.friendly_destination_field, 'Test field')
        self.assertEqual(
            self.tcm.friendly_destination_model_and_field, 'Test Model: Test field'
        )

        self.tcm.ignored = True
        self.assertEqual(self.tcm.friendly_destination_model_and_field, 'Ignored')

        self.tcm.ignored = None
        self.tcm.destination_field = None
        self.assertEqual(self.tcm.friendly_destination_model_and_field, 'Unmapped')

    # will fail as self.destination_django_field is None
    def test_destination_django_field_has_choices(self):
        self.assertTrue(self.tcm.destination_django_field_has_choices)

    # will fail as self.destination_django_field is None
    def test_destination_django_field_choices(self):
        self.assertEqual(self.tcm.destination_django_field_choices, 'test')


class TestDataCoercionMapping(TestCase):

    def setUp(self):
        self.import_record = ImportRecord.objects.create()
        self.file = mock_file_factory('file1.csv')
        self.import_file = ImportFile.objects.create(
            import_record=self.import_record, file=self.file
        )
        self.tcm = TableColumnMapping.objects.create(
            source_string='test', import_file=self.import_file,
            destination_model='TestModel', destination_field='test_field'
        )
        self.dcm = DataCoercionMapping.objects.create(
            source_string='test', table_column_mapping=self.tcm,
            destination_value='test', destination_type='Test'
        )

    def tearDown(self):
        ImportFile.objects.all().delete()
        ImportRecord.objects.all().delete()
        TableColumnMapping.objects.all().delete()
        DataCoercionMapping.objects.all().delete()

    def test_save(self):
        self.dcm.confidence = 1.0
        # this *should* blow up but doesn't becuase someone decided to use a
        # bare except with assert. Facepalm.
        self.dcm.save()
        self.assertTrue(self.dcm.valid_destination_value)
        self.assertTrue(self.dcm.is_mapped)

        # will fail with bare except
        # should raise this as table_column_mapping.destination_django_field
        # was redefined to always be None
        with self.assertRaises(AttributeError):
            self.dcm.confidence = 0.0
            self.dcm.save()

        self.destination_value = None
        self.dcm.save()
        self.assertFalse(self.dcm.valid_destination_value)
        self.assertFalse(self.dcm.is_mapped)

        self.destination_value = None
        self.dcm.save()
        self.assertFalse(self.dcm.valid_destination_value)
        self.assertFalse(self.dcm.is_mapped)


    @mock.patch('seed.data_importer.models.hashlib')
    def test_source_string_sha(self, mock_hashlib):
        mock_hashlib.md5.return_value.hexdigest.return_value = '012345ab'
        self.assertEqual(self.dcm.source_string_sha, '012345ab')
        mock_hashlib.md5.assert_called()
        mock_hashlib.md5.return_value.update.assert_called_with('test')
