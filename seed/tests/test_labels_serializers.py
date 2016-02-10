# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author 'Piper Merriam <pipermerriam@gmail.com>'
"""
"""
Unit tests for map.py
"""

from django.test import TestCase

from seed.lib.superperms.orgs.models import (
    Organization as SuperOrganization,
)
from seed.models import (
    BuildingSnapshot,
    StatusLabel as Label,
    CanonicalBuilding,
)
from seed.serializers.labels import (
    CleansingBuildingLabelsSerializer,
    LabelSerializer,
    UpdateBuildingLabelsSerializer,
)

from seed.factory import SEEDFactory


class TestLabelSerializer(TestCase):
    """Test the label serializer"""

    def test_initialization_requires_organization_as_argument(self):
        with self.assertRaises(KeyError):
            LabelSerializer(building_snapshots=BuildingSnapshot.objects.none())

        organization = SuperOrganization.objects.create(name='test-org')
        LabelSerializer(
            super_organization=organization,
            building_snapshots=BuildingSnapshot.objects.none(),
        )

    def test_initialization_requires_building_snapshots_as_argument(self):
        organization = SuperOrganization.objects.create(name='test-org')

        with self.assertRaises(KeyError):
            LabelSerializer(super_organization=organization)

        LabelSerializer(
            super_organization=organization,
            building_snapshots=BuildingSnapshot.objects.none(),
        )

    def test_uses_provided_organization_over_post_data(self):
        """
        Checks that the serializer doesn't trust a user-provided super
        organization, but rather uses the one determined by the server to
        belong to the user.
        """
        organization_a = SuperOrganization.objects.create(name='test-org-a')
        organization_b = SuperOrganization.objects.create(name='test-org-b')

        data = {
            "name": "test-label-1",
            "color": "red",
            "organization_id": organization_a.pk,
        }
        serializer = LabelSerializer(
            data=data,
            super_organization=organization_b,
            building_snapshots=BuildingSnapshot.objects.none(),
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(
            serializer.validated_data['super_organization'], organization_b
        )

    def test_computed_property_is_applied(self):
        organization = SuperOrganization.objects.create(name='test-org')

        label_a = Label.objects.create(
            color="red", name="test_label-a", super_organization=organization,
        )
        label_b = Label.objects.create(
            color="red", name="test_label-b", super_organization=organization,
        )

        bs = SEEDFactory.building_snapshot(
            canonical_building=CanonicalBuilding.objects.create(),
        )
        bs.canonical_building.labels.add(label_a)

        qs = BuildingSnapshot.objects.all()

        serializer = LabelSerializer(
            label_a,
            super_organization=organization,
            building_snapshots=qs,
        )
        self.assertTrue(serializer.data['is_applied'])

        serializer = LabelSerializer(
            label_b,
            super_organization=organization,
            building_snapshots=qs,
        )
        self.assertFalse(serializer.data['is_applied'])


class TestUpdateBuildingLabelsSerializer(TestCase):
    def test_initialization_requires_organization_as_argument(self):
        with self.assertRaises(KeyError):
            UpdateBuildingLabelsSerializer(
                queryset=CanonicalBuilding.objects.none(),
            )

        organization = SuperOrganization.objects.create(name='test-org')
        UpdateBuildingLabelsSerializer(
            queryset=CanonicalBuilding.objects.none(),
            super_organization=organization,
        )

    def test_initialization_requires_queryset_as_argument(self):
        organization = SuperOrganization.objects.create(name='test-org')

        with self.assertRaises(KeyError):
            UpdateBuildingLabelsSerializer(
                super_organization=organization,
            )

        UpdateBuildingLabelsSerializer(
            super_organization=organization,
            queryset=CanonicalBuilding.objects.none(),
        )

    def test_labels_are_applied(self):
        organization = SuperOrganization.objects.create(name='test-org')

        label_a = Label.objects.create(
            color="red",
            name="label-a",
            super_organization=organization,
        )
        label_b = Label.objects.create(
            color="red",
            name="label-b",
            super_organization=organization,
        )

        bs_1 = SEEDFactory.building_snapshot(
            canonical_building=CanonicalBuilding.objects.create(),
        )
        bs_2 = SEEDFactory.building_snapshot(
            canonical_building=CanonicalBuilding.objects.create(),
        )

        self.assertFalse(bs_1.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertFalse(bs_1.canonical_building.labels.filter(pk=label_b.pk).exists())
        self.assertFalse(bs_2.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertFalse(bs_2.canonical_building.labels.filter(pk=label_b.pk).exists())

        qs = CanonicalBuilding.objects.all()
        self.assertEqual(qs.count(), 2)

        data = {
            'add_label_ids': [label_a.pk, label_b.pk],
            'remove_label_ids': [],
            'selected_buildings': [],
            'select_all_checkbox': True,
        }

        serializer = UpdateBuildingLabelsSerializer(
            data=data,
            super_organization=organization,
            queryset=qs,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save()
        self.assertEqual(qs.count(), 2)

        self.assertTrue(bs_1.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertTrue(bs_1.canonical_building.labels.filter(pk=label_b.pk).exists())
        self.assertTrue(bs_2.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertTrue(bs_2.canonical_building.labels.filter(pk=label_b.pk).exists())

    def test_labels_are_removed(self):
        organization = SuperOrganization.objects.create(name='test-org')

        label_a = Label.objects.create(
            color="red",
            name="label-a",
            super_organization=organization,
        )
        label_b = Label.objects.create(
            color="red",
            name="label-b",
            super_organization=organization,
        )

        bs_1 = SEEDFactory.building_snapshot(
            canonical_building=CanonicalBuilding.objects.create(),
        )
        bs_2 = SEEDFactory.building_snapshot(
            canonical_building=CanonicalBuilding.objects.create(),
        )

        bs_1.canonical_building.labels.add(label_a, label_b)
        bs_2.canonical_building.labels.add(label_b)

        # Sanity check
        self.assertTrue(bs_1.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertTrue(bs_1.canonical_building.labels.filter(pk=label_b.pk).exists())
        self.assertFalse(bs_2.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertTrue(bs_2.canonical_building.labels.filter(pk=label_b.pk).exists())

        qs = CanonicalBuilding.objects.all()
        self.assertEqual(qs.count(), 2)

        data = {
            'add_label_ids': [],
            'remove_label_ids': [label_a.pk, label_b.pk],
            'selected_buildings': [],
            'select_all_checkbox': True,
        }

        serializer = UpdateBuildingLabelsSerializer(
            data=data,
            super_organization=organization,
            queryset=qs,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save()
        self.assertEqual(qs.count(), 2)

        self.assertFalse(bs_1.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertFalse(bs_1.canonical_building.labels.filter(pk=label_b.pk).exists())
        self.assertFalse(bs_2.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertFalse(bs_2.canonical_building.labels.filter(pk=label_b.pk).exists())


class TestCleansingBuildingLabelsSerializer(TestCase):
    def test_initialization_requires_organization_as_argument(self):
        with self.assertRaises(KeyError):
            CleansingBuildingLabelsSerializer(
                queryset=BuildingSnapshot.objects.none(),
            )

        organization = SuperOrganization.objects.create(name='test-org')
        CleansingBuildingLabelsSerializer(
            queryset=BuildingSnapshot.objects.none(),
            super_organization=organization,
        )

    def test_initialization_requires_queryset_as_argument(self):
        organization = SuperOrganization.objects.create(name='test-org')

        with self.assertRaises(KeyError):
            CleansingBuildingLabelsSerializer(
                super_organization=organization,
            )

        CleansingBuildingLabelsSerializer(
            super_organization=organization,
            queryset=BuildingSnapshot.objects.none(),
        )

    def test_labels_are_applied_and_created(self):
        organization = SuperOrganization.objects.create(name='test-org')

        label_a = Label.objects.create(
            color="red",
            name="label-a",
            super_organization=organization,
        )
        label_b = Label.objects.create(
            color="red",
            name="label-b",
            super_organization=organization,
        )

        bs_1 = SEEDFactory.building_snapshot()
        bs_2 = SEEDFactory.building_snapshot()

        data = {
            'label_ids': [label_a.pk, label_b.pk],
            'building_ids': [bs_1.pk, bs_2.pk],
            'updates': [
                {
                    'label_id': label_a.pk,
                    'add_to_building_ids': [bs_1.pk]
                },
                {
                    'label_id': label_b.pk,
                    'add_to_building_ids': [bs_2.pk]
                },
                { 
                    'label_id': None,
                    'label_name': "new label",
                    'label_color': "red",
                    'add_to_building_ids' : [bs_2.pk]
                }
            ],
        }

        serializer = CleansingBuildingLabelsSerializer(
            data=data,
            super_organization=organization,
            queryset=BuildingSnapshot.objects.all(),
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)

        serializer.save()

        # Make sure new label was created.
        self.assertEqual(3, Label.objects.all().count())

        bs_1 = BuildingSnapshot.objects.get(pk=bs_1.pk)
        bs_2 = BuildingSnapshot.objects.get(pk=bs_2.pk)

        self.assertTrue(bs_1.canonical_building.labels.filter(pk=label_a.pk).exists())
        self.assertTrue(bs_2.canonical_building.labels.filter(pk=label_b.pk).exists())

        # Make sure building 2 has 2 labels, label_b, and new one
        self.assertTrue(2, bs_2.canonical_building.labels.all().count())
