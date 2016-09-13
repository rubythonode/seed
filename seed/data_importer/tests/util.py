# !/usr/bin/env python
# encoding: utf-8
"""
:copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.  # NOQA
:author
"""
import csv
import json
import logging
import os
from os import path

from django.core.files import File

from seed.data_importer.models import ImportFile, ImportRecord
from seed.data_importer.tasks import save_raw_data, map_data
from seed.landing.models import SEEDUser as User
from seed.lib.superperms.orgs.models import Organization, OrganizationUser
from seed.models import (
    Column,
    DATA_STATE_IMPORT,
    ASSESSED_RAW
)

logger = logging.getLogger(__name__)


def load_test_data(test_obj, filename):
    """
    Load some test data for running tests

    Args:
        test_obj: The test object (typically self)
        filename: Name of the file to load in tests/data directory

    Returns:

    """
    test_obj.maxDiff = None
    test_obj.import_filename = filename
    test_obj.fake_user = User.objects.create(username='test')
    test_obj.import_record = ImportRecord.objects.create(
        owner=test_obj.fake_user,
        last_modified_by=test_obj.fake_user
    )
    test_obj.import_file = ImportFile.objects.create(
        import_record=test_obj.import_record
    )
    test_obj.import_file.is_espm = True
    test_obj.import_file.source_type = 'PORTFOLIO_RAW'
    test_obj.import_file.data_state = DATA_STATE_IMPORT
    f = path.join(path.dirname(__file__), 'data', filename)
    test_obj.import_file.file = File(open(f))
    test_obj.import_file.save()

    # Mimic the representation in the PM file. #ThanksAaron
    # This is the last row of the portfolio manager file
    test_obj.fake_extra_data = {
        u'City': u'EnergyTown',
        u'ENERGY STAR Score': u'',
        u'State/Province': u'Illinois',
        u'Site EUI (kBtu/ft2)': u'',
        u'Year Ending': u'',
        u'Weather Normalized Source EUI (kBtu/ft2)': u'',
        u'Parking - Gross Floor Area (ft2)': u'',
        u'Address 1': u'000015581 SW Sycamore Court',
        u'Property Id': u'101125',
        u'Address 2': u'Not Available',
        u'Source EUI (kBtu/ft2)': u'',
        u'Release Date': u'',
        u'National Median Source EUI (kBtu/ft2)': u'',
        u'Weather Normalized Site EUI (kBtu/ft2)': u'',
        u'National Median Site EUI (kBtu/ft2)': u'',
        u'Year Built': u'',
        u'Postal Code': u'10108-9812',
        u'Organization': u'Occidental Management',
        u'Property Name': u'Not Available',
        u'Property Floor Area (Buildings and Parking) (ft2)': u'',
        u'Total GHG Emissions (MtCO2e)': u'',
        u'Generation Date': u'',
    }
    test_obj.fake_row = {
        u'Name': u'The Whitehouse',
        u'Address Line 1': u'1600 Pennsylvania Ave.',
        u'Year Built': u'1803',
        u'Double Tester': 'Just a note from bob'
    }

    test_obj.fake_org = Organization.objects.create()
    OrganizationUser.objects.create(
        user=test_obj.fake_user,
        organization=test_obj.fake_org
    )

    test_obj.import_record.super_organization = test_obj.fake_org
    test_obj.import_record.save()

    test_obj.fake_mappings = {
        'property_name': u'Name',
        'address_line_1': u'Address Line 1',
        'year_built': u'Year Built'
    }

    return test_obj


def import_example_data(test_obj, filename):
    """
    Import example spreadsheets that contain the 4 cases to test the
    new data model.

    Args:
        test_obj: test object to add data to
        filename: name of the file to import

    Returns:
        test_obj

    """

    test_obj.fake_user = User.objects.create(username='test')
    test_obj.fake_org = Organization.objects.create()

    # Create an org user
    OrganizationUser.objects.create(
        user=test_obj.fake_user,
        organization=test_obj.fake_org
    )

    test_obj.import_record = ImportRecord.objects.create(
        owner=test_obj.fake_user,
        last_modified_by=test_obj.fake_user,
        super_organization=test_obj.fake_org
    )
    test_obj.import_file = ImportFile.objects.create(
        import_record=test_obj.import_record
    )
    test_obj.import_file.is_espm = True
    test_obj.import_file.source_type = ASSESSED_RAW
    test_obj.import_file.data_state = DATA_STATE_IMPORT

    f = path.join(path.dirname(__file__), 'data', filename)
    test_obj.import_file.file = File(open(f))
    test_obj.import_file.save()

    save_raw_data(test_obj.import_file.id)

    # setup the mapping
    properties_mapping = [
        {
            "from_field": u'jurisdiction_taxlot_identifier',
            "to_table_name": u'TaxLotState',
            "to_field": u'jurisdiction_taxlot_identifier',
        }, {
            "from_field": u'jurisdiction_property_identifier',
            "to_table_name": u'PropertyState',
            "to_field": u'jurisdiction_property_identifier',
        }, {
            "from_field": u'building_portfolio_manager_identifier',
            "to_table_name": u'PropertyState',
            "to_field": u'building_portfolio_manager_identifier',
        }, {
            "from_field": u'pm_parent_property_id',
            "to_table_name": u'PropertyState',
            "to_field": u'pm_parent_property_id'
        }, {
            "from_field": u'address_line_1',
            "to_table_name": u'PropertyState',
            "to_field": u'address_line_1'
        }, {
            "from_field": u'city',
            "to_table_name": u'PropertyState',
            "to_field": u'city'
        }, {
            "from_field": u'property_name',
            "to_table_name": u'PropertyState',
            "to_field": u'property_name'
        }, {
            "from_field": u'property_notes',
            "to_table_name": u'PropertyState',
            "to_field": u'property_notes'
        }, {
            "from_field": u'use_description',
            "to_table_name": u'PropertyState',
            "to_field": u'use_description'
        }, {
            "from_field": u'gross_floor_area',
            "to_table_name": u'PropertyState',
            "to_field": u'gross_floor_area'
        }, {
            "from_field": u'owner',
            "to_table_name": u'PropertyState',
            "to_field": u'owner'
        }, {
            "from_field": u'owner_email',
            "to_table_name": u'PropertyState',
            "to_field": u'owner_email'
        }, {
            "from_field": u'owner_telephone',
            "to_table_name": u'PropertyState',
            "to_field": u'owner_telephone'
        }, {
            "from_field": u'site_eui',
            "to_table_name": u'PropertyState',
            "to_field": u'site_eui'
        }, {
            "from_field": u'energy_score',
            "to_table_name": u'PropertyState',
            "to_field": u'energy_score'
        }, {
            "from_field": u'year_ending',
            "to_table_name": u'PropertyState',
            "to_field": u'year_ending'
        }
    ]

    Column.create_mappings(properties_mapping, test_obj.fake_org, test_obj.fake_user)

    # call the mapping function from the tasks file
    map_data(test_obj.import_file.id)

    # print len(PropertyState.objects.all())

    # This is the last row of the portfolio manager file
    test_obj.fake_extra_data = {
        u'City': u'EnergyTown',
        u'ENERGY STAR Score': u'',
        u'State/Province': u'Illinois',
        u'Site EUI (kBtu/ft2)': u'',
        u'Year Ending': u'',
        u'Weather Normalized Source EUI (kBtu/ft2)': u'',
        u'Parking - Gross Floor Area (ft2)': u'',
        u'Address 1': u'000015581 SW Sycamore Court',
        u'Property Id': u'101125',
        u'Address 2': u'Not Available',
        u'Source EUI (kBtu/ft2)': u'',
        u'Release Date': u'',
        u'National Median Source EUI (kBtu/ft2)': u'',
        u'Weather Normalized Site EUI (kBtu/ft2)': u'',
        u'National Median Site EUI (kBtu/ft2)': u'',
        u'Year Built': u'',
        u'Postal Code': u'10108-9812',
        u'Organization': u'Occidental Management',
        u'Property Name': u'Not Available',
        u'Property Floor Area (Buildings and Parking) (ft2)': u'',
        u'Total GHG Emissions (MtCO2e)': u'',
        u'Generation Date': u'',
    }
    test_obj.fake_row = {
        u'Name': u'The Whitehouse',
        u'Address Line 1': u'1600 Pennsylvania Ave.',
        u'Year Built': u'1803',
        u'Double Tester': 'Just a note from bob'
    }

    test_obj.import_record.super_organization = test_obj.fake_org
    test_obj.import_record.save()

    test_obj.fake_mappings = {
        'property_name': u'Name',
        'address_line_1': u'Address Line 1',
        'year_built': u'Year Built'
    }

    return test_obj


def import_exported_test_data(test_obj, filename):
    """
    Import test files from Stephen for many-to-many testing. This imports and
    maps the data accordingly. Presently these files are missing a couple
    attributes to make them valid: 1) need the master campus record to define
    the pm_property_id, 2) the joins between propertystate and taxlotstate
    seem to be missing

        Args:
            test_obj: test object to add data to
            filename: name of the file to import in the new format

        Returns:
            test_obj
    """

    test_obj.fake_user = User.objects.create(username='test')
    test_obj.fake_org = Organization.objects.create()
    # Create an org user
    OrganizationUser.objects.create(user=test_obj.fake_user, organization=test_obj.fake_org)

    test_obj.import_record = ImportRecord.objects.create(
        owner=test_obj.fake_user,
        last_modified_by=test_obj.fake_user,
        super_organization=test_obj.fake_org
    )
    test_obj.import_file = ImportFile.objects.create(import_record=test_obj.import_record)
    test_obj.import_file.is_espm = True
    test_obj.import_file.source_type = ASSESSED_RAW
    test_obj.import_file.data_state = DATA_STATE_IMPORT

    # Do a bunch of work to flatten out this temp file that has extra_data as
    # a string representation of a dict
    data = []
    keys = None
    new_keys = set()

    f = path.join(path.dirname(__file__), 'data', filename)
    with open(f, 'rb') as csvfile:
        reader = csv.DictReader(csvfile)
        keys = reader.fieldnames
        for row in reader:
            ed = json.loads(row.pop('extra_data'))
            for k, v in ed.iteritems():
                new_keys.add(k)
                row[k] = v
            data.append(row)

    # remove the extra_data column and add in the new columns
    keys.remove('extra_data')
    for k in new_keys:
        keys.append(k)

    # save the new file
    new_file_name = 'tmp_' + os.path.splitext(os.path.basename(filename))[0] + '_flat.csv'
    f_new = path.join(path.dirname(__file__), 'data', new_file_name)
    with open(f_new, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        for d in data:
            writer.writerow(d)

    # save the keys
    new_file_name = 'tmp_' + os.path.splitext(os.path.basename(filename))[0] + '_keys.csv'
    f_new = path.join(path.dirname(__file__), 'data', new_file_name)
    with open(f_new, 'w') as outfile:
        for item in keys:
            print>> outfile, item

    # Continue saving the raw data
    new_file_name = 'tmp_' + os.path.splitext(os.path.basename(filename))[0] + '_flat.csv'
    f_new = path.join(path.dirname(__file__), 'data', new_file_name)
    test_obj.import_file.file = File(open(f_new))
    test_obj.import_file.save()

    save_raw_data(test_obj.import_file.id)

    # for ps in PropertyState.objects.all():
    #     print ps.__dict__

    # the mapping is just the 'keys' repeated since the file was created as a
    # database dump
    mapping = []
    for k in keys:
        if k == 'id':
            continue
        mapping.append(
            {
                "from_field": k,
                "to_table_name": "PropertyState",
                "to_field": k
            }
        )

    Column.create_mappings(mapping, test_obj.fake_org, test_obj.fake_user)

    # call the mapping function from the tasks file
    map_data(test_obj.import_file.id)

    # print len(PropertyState.objects.all())

    # Mimic the representation in the PM file. #ThanksAaron
    # This is the last row of the portfolio manager file
    test_obj.fake_extra_data = {
        u'City': u'EnergyTown',
        u'ENERGY STAR Score': u'',
        u'State/Province': u'Illinois',
        u'Site EUI (kBtu/ft2)': u'',
        u'Year Ending': u'',
        u'Weather Normalized Source EUI (kBtu/ft2)': u'',
        u'Parking - Gross Floor Area (ft2)': u'',
        u'Address 1': u'000015581 SW Sycamore Court',
        u'Property Id': u'101125',
        u'Address 2': u'Not Available',
        u'Source EUI (kBtu/ft2)': u'',
        u'Release Date': u'',
        u'National Median Source EUI (kBtu/ft2)': u'',
        u'Weather Normalized Site EUI (kBtu/ft2)': u'',
        u'National Median Site EUI (kBtu/ft2)': u'',
        u'Year Built': u'',
        u'Postal Code': u'10108-9812',
        u'Organization': u'Occidental Management',
        u'Property Name': u'Not Available',
        u'Property Floor Area (Buildings and Parking) (ft2)': u'',
        u'Total GHG Emissions (MtCO2e)': u'',
        u'Generation Date': u'',
    }
    test_obj.fake_row = {
        u'Name': u'The Whitehouse',
        u'Address Line 1': u'1600 Pennsylvania Ave.',
        u'Year Built': u'1803',
        u'Double Tester': 'Just a note from bob'
    }

    test_obj.import_record.super_organization = test_obj.fake_org
    test_obj.import_record.save()

    # setup the mapping
    test_obj.fake_mappings = [
        {
            "from_field": u'Year Built',
            "to_table_name": u'PropertyState',
            "to_field": u'year_built',
        }, {
            "from_field": u'Address Line 1',
            "to_table_name": u'PropertyState',
            "to_field": u'address_line_1',
        }, {
            "from_field": u'Name',
            "to_table_name": u'PropertyState',
            "to_field": u'property_name'
        }
    ]

    return test_obj
