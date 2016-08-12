from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from seed.lib.superperms.orgs.models import Organization
import datetime
import logging
import itertools
import seed.models

from seed.test_helpers.fake import FakePropertyStateFactory, FakeTaxLotStateFactory, BaseFake

logging.basicConfig(level=logging.DEBUG)
_log = logging.getLogger(__name__)

BUILDING_USE = ('Hospital', 'Hotel', 'Office', 'University', 'Retail')

USE_CLASS = ('A', 'B', 'C', 'D', 'E')

COMPLIANCE = ('Y', 'N')

# Just a list of counties to pick from.
COUNTIES = ("Los Angeles County", "Orange County", "San Diego County", "Riverside County",
            "San Bernardino County", "Santa Clara County", "Alameda County", "Sacramento County",
            "Contra Costa County", "Fresno County", "Ventura County", "San Francisco County",
            "Kern County", "San Mateo County", "San Joaquin County", "Stanislaus County",
            "Sonoma County", "Tulare County", "Solano County", "Monterey County", "Santa Barbara County",
            "Placer County", "San Luis Obispo County", "Santa Cruz County", "Merced County",
            "Marin County", "Butte County", "Yolo County", "El Dorado County", "Shasta County",
            "Imperial County", "Kings County", "Madera County", "Napa County", "Humboldt County",
            "Nevada County", "Sutter County", "Mendocino County", "Yuba County", "Lake County",
            "Tehama County", "Tuolumne County", "San Benito County", "laveras County", "Siskiyou County",
            "Amador County", "Lassen County", "Del Norte County", "Glenn County", "Plumas County",
            "Colusa County", "Mariposa County", "Inyo County", "Trinity County", "Mono County",
            "Modoc County", "Sierra County", "Alpine County")


# Due to the way extra data was being handled regarding record creation
# it seemed most expedient to just define a temporary class
# to hold both normal and extra data for later.
class SampleDataRecord(object):
    def __init__(self, data, extra_data):
        self.data = data
        self.extra_data = extra_data


class FakePropertyStateExtraDataFactory(BaseFake):
    """
    Factory Class for producing extra data dict for PropertyState
    """

    def __init__(self):
        super(FakePropertyStateExtraDataFactory, self).__init__()

    def property_state_extra_data_details(self, id, organization):
        property_extra_data = {"CoStar Property ID": self.fake.numerify(text='#######'),
                               "Organization": organization.name,
                               "Compliance Required": self.fake.random_element(elements=COMPLIANCE),
                               "County": self.fake.random_element(elements=COUNTIES),
                               "Date / Last Personal Correspondence": self.fake.date(pattern='%m/%d/%Y'),
                               "property_extra_data_field_1": "property_extra_data_field_" + str(id),
                               "Does Not Need to Comply": self.fake.random_element(elements=COMPLIANCE)}

        return property_extra_data

    def property_state_extra_data(self, id, organization, **kw):
        """Return a property state populated with pseudo random data"""
        ps = self.property_state_extra_data_details(id, organization)
        ps.update(kw)
        return ps


class CreateSampleDataFakePropertyStateFactory(FakePropertyStateFactory):
    """
    Factory Class for producing PropertyState dict
    """

    def __init__(self, organization, year_ending, case_description, extra_data_factory):
        super(CreateSampleDataFakePropertyStateFactory, self).__init__()

        self.organization = organization
        self.year_ending = year_ending
        self.case_description = case_description
        self.extra_data_factory = extra_data_factory

    def property_state_details(self):
        """Return a dict of pseudo random data for use with PropertyState"""
        owner = self.owner()
        property = self.get_details()

        building_portfolio_manager_identifier = self.fake.numerify(text='#######')
        extra_data = self.extra_data_factory.property_state_extra_data(building_portfolio_manager_identifier, self.organization)

        # This field was not in case A, B, or C for Robin's original examples so removing it from the
        # dict.  Case D handles this itself.
        fields_to_remove = ["pm_parent_property_id"]
        for field in fields_to_remove:
            del property[field]

        # Add in fields that were in Robin's original examples but are not in the base factory.
        data_not_in_base = {"building_portfolio_manager_identifier": building_portfolio_manager_identifier,
                            "property_name": owner.name + "'s " + self.fake.random_element(elements=BUILDING_USE),
                            "use_description": self.fake.random_element(elements=BUILDING_USE),
                            "energy_score": self.fake.numerify(text='##'),
                            "site_eui": self.fake.numerify(text='###.#'),
                            "year_ending": self.year_ending,
                            "gross_floor_area": self.fake.numerify(text='#######'),
                            "property_notes": self.case_description}

        property.update(data_not_in_base)

        property_record = SampleDataRecord(property, extra_data)
        return property_record

    def property_state(self, **kw):
        """Return a property state dict populated with pseudo random data"""
        ps = self.property_state_details()
        ps.data.update(kw)
        return ps


class FakeTaxLotExtraDataFactory(BaseFake):
    """
    Factory Class for producing extra data dict for TaxLotState
    """

    def __init__(self):
        super(FakeTaxLotExtraDataFactory, self).__init__()

    def tax_lot_extra_data_details(self, id, year_ending):
        """Return a dict of pseudo random data for use with Building Snapshot"""
        owner = self.owner()

        tl = {"Owner City": self.fake.city(),
              "Tax Year": year_ending,
              "Parcel Gross Area": self.fake.numerify(text='####-###'),
              "Use Class": self.fake.random_element(elements=USE_CLASS),
              "Ward": self.fake.numerify(text='#'),
              "X Coordinate": self.fake.latitude(),
              "Y Coordinate": self.fake.longitude(),
              "Owner Name": owner.name,
              "Owner Address": self.address_line_1(),
              "Owner State": self.fake.state_abbr(),
              "Owner Zip": self.fake.zipcode(),
              "Tax Class": self.fake.random_element(elements=USE_CLASS) + self.fake.numerify(text='#'),
              "taxlot_extra_data_field_1": "taxlot_extra_data_field_" + str(id),
              "City Code": self.fake.numerify(text='####-###')}

        return tl

    def tax_lot_extra_data(self, id, year_ending, **kw):
        """Return a tax state dict populated with pseudo random data"""
        tl = self.tax_lot_extra_data_details(id, year_ending)
        tl.update(kw)
        return tl


class CreateSampleDataFakeTaxLotFactory(FakeTaxLotStateFactory):
    """
    Factory Class for producing Building Snaphots.
    """

    def __init__(self, organization, extra_data_factory):
        super(CreateSampleDataFakeTaxLotFactory, self).__init__()
        self.extra_data_factory = extra_data_factory

    def tax_lot_details(self):
        tl = self.get_details()
        jurisdiction_taxlot_identifier = self.fake.numerify(text='########')

        # Add in fields that were in Robin's original examples but are not in the base factory.
        data_not_in_base = {"jurisdiction_taxlot_identifier": jurisdiction_taxlot_identifier,
                            "address": self.address_line_1(),
                            "city": self.fake.city()}

        tl.update(data_not_in_base)
        extra_data = self.extra_data_factory.tax_lot_extra_data(jurisdiction_taxlot_identifier, self.fake.random_int(min=2010, max=2015))

        tax_lot_record = SampleDataRecord(tl, extra_data)
        return tax_lot_record

    def tax_lot(self, **kw):
        """Return a property state populated with pseudo random data"""
        tl = self.tax_lot_details()
        tl.data.update(kw)
        return tl


def create_cycle(org):
    seed.models.Cycle.objects.get_or_create(name="2015 Annual",
                                            organization=org,
                                            start=datetime.datetime(2015, 1, 1),
                                            end=datetime.datetime(2016, 1, 1) - datetime.timedelta(seconds=1))
    return


def create_cases(org, tax_lots, properties):
    cycle = seed.models.Cycle.objects.filter(organization=org).first()

    for (tl_rec, prop_rec) in itertools.product(tax_lots, properties):
        tl_def = tl_rec.data
        prop_def = prop_rec.data
        tl_extra_data = tl_rec.extra_data
        prop_extra_data = prop_rec.extra_data

        # states don't have an org and since this script was doing all buildings twice
        # (once for individual, once for _caseALL).  So if the get_or_create returns
        # an existing one then it still is unknown if it is something that already exists.
        # Check the view model to see if there is something with this state and this org.
        # If it doesn't exist thencreate one.  If it does exist than that is correct (hopefully)
        #
        # FIXME.  In the instance where this script is creating both individual cases and _caseALL this
        # throws an error for some taxlots that multiple are returned.  Since TaxLotState does not depend
        # on an org I think this might have to go something like filter the view for this org and a state that
        # has fields that match **state_def.  However per Robin we are OK just restricting things to
        # the _caseALLL case for now so this is not currently a problem.
        def _create_state(view_model, state_model, org, state_def):
            state, created = state_model.objects.get_or_create(**state_def)
            if not created and not view_model.objects.filter(state=state).filter(cycle__organization=org).exists():
                state = state_model.objects.create(**state_def)
                created = True
            return state, created

        prop_state, property_state_created = _create_state(seed.models.PropertyView,
                                                           seed.models.PropertyState,
                                                           org,
                                                           prop_def)

        for k, v in prop_extra_data.items():
            prop_state.extra_data[k] = v

        prop_state.save()

        taxlot_state, taxlot_state_created = _create_state(seed.models.TaxLotView,
                                                           seed.models.TaxLotState,
                                                           org,
                                                           tl_def)

        for k, v in tl_extra_data.items():
            taxlot_state.extra_data[k] = v

        taxlot_state.save()

        # Moved the property and taxlot items below the state items because they only depend on an org
        # So if they are just left at the top as get_or_create(organization=org) then there will only
        # be one property created per org.  Instead for creating this data if the state was created
        # then a property/taxlot needs to be created too.
        if property_state_created:
            property = seed.models.Property.objects.create(organization=org)
        else:
            # else the propery_state already existed so there should also be a PropertyView
            # with this with this property_state.  Find and use that property.
            property = seed.models.PropertyView.objects.filter(state=prop_state).filter(property__organization=org)[0].property

        if taxlot_state_created:
            taxlot = seed.models.TaxLot.objects.create(organization=org)
        else:
            # else the taxlot_state already existed so there should also be a TaxlotView
            # with this with this taxlot_state.  Find and use that taxlot.
            taxlot = seed.models.TaxLotView.objects.filter(state=taxlot_state).filter(taxlot__organization=org)[0].taxlot

        taxlot_view, created = seed.models.TaxLotView.objects.get_or_create(taxlot=taxlot, cycle=cycle, state=taxlot_state)
        prop_view, created = seed.models.PropertyView.objects.get_or_create(property=property, cycle=cycle, state=prop_state)

        tlp, created = seed.models.TaxLotProperty.objects.get_or_create(property_view=prop_view, taxlot_view=taxlot_view, cycle=cycle)

    return


# For all cases make it so the city is the same within a case.  Not strictly required but
# it is more realistic
def create_case_A(org, taxlot_factory, property_factory):

        tl = taxlot_factory.tax_lot()
        prop = property_factory.property_state(address_line_1=tl.data["address"], city=tl.data["city"])

        create_cases(org, [tl], [prop])


def create_case_B(org, taxlot_factory, property_factory, number_properties=3):

    taxlots = [taxlot_factory.tax_lot()]

    properties = []
    for i in range(number_properties):
        properties.append(property_factory.property_state(city=taxlots[0].data["city"]))

    create_cases(org, taxlots, properties)


def create_case_C(org, taxlot_factory, property_factory, number_taxlots=3):

    properties = [property_factory.property_state()]

    taxlots = []
    for i in range(number_taxlots):
        taxlots.append(taxlot_factory.tax_lot(city=properties[0].data["city"]))

    create_cases(org, taxlots, properties)


def create_case_D(org, taxlot_factory, property_factory):

    campus = property_factory.property_state()
    city = campus.data["city"]
    campus.data["pm_parent_property_id"] = campus.data["building_portfolio_manager_identifier"]

    campus_property_id = campus.data["pm_parent_property_id"]

    taxlots = []
    for i in range(3):
        taxlots.append(taxlot_factory.tax_lot(city=city))

    properties = []
    for i in range(5):
        properties.append(property_factory.property_state(pm_parent_property_id=campus_property_id, city=city))

    cycle = seed.models.Cycle.objects.filter(organization=org).first()

    def add_extra_data(state, extra_data):
        if not extra_data:
            return state

        for k in extra_data:
            state.extra_data[k] = extra_data[k]
        state.save()
        return state

    campus_property = seed.models.Property.objects.create(organization=org, campus=True)
    property_objs = [seed.models.Property.objects.create(organization=org, parent_property=campus_property) for p in properties]

    property_objs.insert(0, campus_property)
    taxlot_objs = [seed.models.TaxLot.objects.create(organization=org) for t in taxlots]

    def _create_states_with_extra_data(model, records):
        states = []
        for rec in records:
            state = model.objects.get_or_create(**rec.data)[0]
            state = add_extra_data(state, rec.extra_data)
            states.append(state)
        return states

    property_states = _create_states_with_extra_data(seed.models.PropertyState, [campus] + properties)
    property_views = [seed.models.PropertyView.objects.get_or_create(property=property, cycle=cycle, state=prop_state)[0] for (property, prop_state) in zip(property_objs, property_states)]

    taxlot_states = _create_states_with_extra_data(seed.models.TaxLotState, taxlots)
    taxlot_views = [seed.models.TaxLotView.objects.get_or_create(taxlot=taxlot, cycle=cycle, state=taxlot_state)[0] for (taxlot, taxlot_state) in zip(taxlot_objs, taxlot_states)]

    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[0], taxlot_view=taxlot_views[0], cycle=cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[1], taxlot_view=taxlot_views[0], cycle=cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[2], taxlot_view=taxlot_views[0], cycle=cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[3], taxlot_view=taxlot_views[0], cycle=cycle)

    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[4], taxlot_view=taxlot_views[1], cycle=cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[4], taxlot_view=taxlot_views[2], cycle=cycle)

    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[5], taxlot_view=taxlot_views[1], cycle=cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view=property_views[5], taxlot_view=taxlot_views[2], cycle=cycle)

    return


def create_sample_data(a_ct=0, b_ct=0, c_ct=0, d_ct=0):
    org, _ = Organization.objects.get_or_create(name="SampleDataDemo_caseALL")
    create_cycle(org)
    year_ending = datetime.datetime(2015, 1, 1)

    taxlot_extra_data_factory = FakeTaxLotExtraDataFactory()
    taxlot_factory = CreateSampleDataFakeTaxLotFactory(org, taxlot_extra_data_factory)
    property_extra_data_factory = FakePropertyStateExtraDataFactory()
    property_factory = CreateSampleDataFakePropertyStateFactory(org, year_ending, "Case A-1: 1 Property, 1 Tax Lot", property_extra_data_factory)

    for i in range(a_ct):
        print "Creating Case A {i}".format(i=i)
        create_case_A(org, taxlot_factory, property_factory)

    for i in range(b_ct):
        print "Creating Case B {i}".format(i=i)
        property_factory.case_description = "Case B-1: Multiple (3) Properties, 1 Tax Lot"
        create_case_B(org, taxlot_factory, property_factory)

    for i in range(c_ct):
        print "Creating Case C {i}".format(i=i)
        property_factory.case_description = "Case C: 1 Property, Multiple (3) Tax Lots"
        create_case_C(org, taxlot_factory, property_factory)

    for i in range(d_ct):
        print "Creating Case D {i}".format(i=i)
        property_factory.case_description = "Case D: Campus with Multiple associated buildings"
        create_case_D(org, taxlot_factory, property_factory)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--A', dest='case_A_count', default=False)
        parser.add_argument('--B', dest='case_B_count', default=False)
        parser.add_argument('--C', dest='case_C_count', default=False)
        parser.add_argument('--D', dest='case_D_count', default=False)
        return

    def handle(self, *args, **options):
        create_sample_data(int(options.get("case_A_count", 0)),
                           int(options.get("case_B_count", 0)),
                           int(options.get("case_C_count", 0)),
                           int(options.get("case_D_count", 0)))
        return
