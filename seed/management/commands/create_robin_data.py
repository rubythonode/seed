from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from seed.lib.superperms.orgs.models import Organization
import datetime
import logging
import itertools
import seed.models

logging.basicConfig(level=logging.DEBUG)


# tax_lot_columns = tax_lot_extra_data_map.keys()[0]
# property_columns = property_extra_data_map.keys()[0]

tax_lot_extra_data_map = {}
tax_lot_extra_data_map["1552813"] = {"Owner City": "Rust",
                                     "Tax Year": "2012",
                                     "Parcel Gross Area": "25522",
                                     "Use Class": "Hotel",
                                     "Ward": "5",
                                     "X Coordinate": "",
                                     "Y Coordinate": "",
                                     "Owner Name": "Univerity Inn LLC",
                                     "Owner Address": "50 Willow Ave SE",
                                     "Owner State": "CA",
                                     "Owner Zip": "94930",
                                     "Tax Class": "5",
                                     "taxlot_extra_data_field_1": "taxlot_extra_data_field_1552813",
                                     "City Code": "392-129"}

tax_lot_extra_data_map["11160509"] = {"Owner City": "Cleveland",
                                      "Tax Year": "2015",
                                      "Parcel Gross Area": "2,000,000",
                                      "Use Class": "Mixed Use",
                                      "Ward": "6",
                                      "X Coordinate": "",
                                      "Y Coordinate": "",
                                      "Owner Name": "Shops R Us LLC",
                                      "Owner Address": "39200 Wilmington Blvd",
                                      "Owner State": "OH",
                                      "Owner Zip": "93029",
                                      "Tax Class": "4",
                                      "taxlot_extra_data_field_1": "taxlot_extra_data_field_11160509",
                                      "City Code": "502-561"}

tax_lot_extra_data_map["33366555"] =  {"Owner City": "Seattle",
                                       "Tax Year": "2016",
                                       "Parcel Gross Area": "500,000",
                                       "Use Class": "School",
                                       "Ward": "2",
                                       "X Coordinate": "",
                                       "Y Coordinate": "",
                                       "Owner Name": "Montessori Inc",
                                       "Owner Address": "555 East Shore Hwy",
                                       "Owner State": "WA",
                                       "Owner Zip": "",
                                       "Tax Class": "4",
                                       "taxlot_extra_data_field_1": "taxlot_extra_data_field_33366555",
                                       "City Code": "562-123"}



tax_lot_extra_data_map["33366125"] = {"Owner City": "Rust",
                                      "Tax Year": "2011",
                                      "Parcel Gross Area": "25,000",
                                      "Use Class": "School",
                                      "Ward": "2",
                                      "X Coordinate": "",
                                      "Y Coordinate": "",
                                      "Owner Name": "Harry Wills",
                                      "Owner Address": "31 Main",
                                      "Owner State": "CA",
                                      "Owner Zip": "",
                                      "Tax Class": "2",
                                      "taxlot_extra_data_field_1": "taxlot_extra_data_field_33366125",
                                      "City Code": "612-846"}

tax_lot_extra_data_map["33366148"] = {"Owner City": "Seattle",
                                      "Tax Year": "2015",
                                      "Parcel Gross Area": "10,000",
                                      "Use Class": "School",
                                      "Ward": "2",
                                      "X Coordinate": "",
                                      "Y Coordinate": "",
                                      "Owner Name": "Loretta Wilkins",
                                      "Owner Address": "3311253 Highway 56",
                                      "Owner State": "WA",
                                      "Owner Zip": "",
                                      "Tax Class": "4",
                                      "taxlot_extra_data_field_1": "taxlot_extra_data_field_33366148",
                                      "City Code": "955-225N"}

property_extra_data_map = {}
property_extra_data_map[2264] = { "CoStar Property ID": "2312456",
                                  "Organization": "",
                                  "Compliance Required": "Y",
                                  "County": "Contra Costa",
                                  "Date / Last Personal Correspondence": "2/5/2016",
                                  "property_extra_data_field_1": "property_extra_data_field_2254",
                                  "Does Not Need to Comply": "" }

property_extra_data_map[3020139] = {"CoStar Property ID" : "2453125",
                                    "Organization" : "",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "5/6/2016",
                                    "property_extra_data_field_1": "property_extra_data_field_3020139",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[4828379] = {"CoStar Property ID" : "1245683",
                                    "Organization" : "",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "5/12/2016",
                                    "property_extra_data_field_1": "property_extra_data_field_4828379",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1154623] = {"CoStar Property ID" : "4467856",
                                    "Organization" : "",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "5/6/2016",
                                    "property_extra_data_field_1": "property_extra_data_field_1154623",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[5233255] = {"CoStar Property ID" : "1234856",
                                    "Organization" : "",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "3/15/2016",
                                    "property_extra_data_field_1": "property_extra_data_field_5233255",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1311523] = {"CoStar Property ID" : "5412648",
                                    "Organization" : "Lucky University",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "",
                                    "property_extra_data_field_1": "property_extra_data_field_1311523",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1311524] = {"CoStar Property ID" : "5123456",
                                    "Organization" : "Lucky University",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "",
                                    "property_extra_data_field_1": "property_extra_data_field_1311524",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1311525] = {"CoStar Property ID" : "2154532",
                                    "Organization" : "Lucky University",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "",
                                    "property_extra_data_field_1": "property_extra_data_field_1311525",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1311526] = {"CoStar Property ID" : "754863",
                                    "Organization" : "Lucky University",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "",
                                    "property_extra_data_field_1": "property_extra_data_field_1311526",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1311527] = {"CoStar Property ID" : "1154286",
                                    "Organization" : "Lucky University",
                                    "Compliance Required" : "Y",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "5/5/2015",
                                    "property_extra_data_field_1": "property_extra_data_field_1311527",
                                    "Does Not Need to Comply" : ""}

property_extra_data_map[1311528] = {"CoStar Property ID" : "2145954",
                                    "Organization" : "",
                                    "Compliance Required" : "N",
                                    "County" : "",
                                    "Date / Last Personal Correspondence" : "",
                                    "property_extra_data_field_1": "property_extra_data_field_1311528",
                                    "Does Not Need to Comply" : "X"}

property_extra_data_map[6798215] = {"CoStar Property ID" : "",
                                    "Organization" : "",
                                    "Compliance Required" : "",
                                    "County" : "Contra Costa",
                                    "Date / Last Personal Correspondence" : "",
                                    "property_extra_data_field_1": "extra_data_field_6798215",
                                    "Does Not Need to Comply" : ""}

def create_individual_orgs():
    org, _ = Organization.objects.get_or_create(name = "SampleDataDemo_caseA")
    create_cycle(org)
    create_case_A_objects(org)

    org, _ = Organization.objects.get_or_create(name = "SampleDataDemo_caseB")
    create_cycle(org)
    create_case_B_objects(org)

    org, _ = Organization.objects.get_or_create(name = "SampleDataDemo_caseC")
    create_cycle(org)
    create_case_C_objects(org)

    org, _ = Organization.objects.get_or_create(name = "SampleDataDemo_caseD")
    create_cycle(org)
    create_case_D_objects(org)

    return
    
def create_one_org_with_all_cases():
    org, _ = Organization.objects.get_or_create(name = "SampleDataDemo_caseALL")
    create_cycle(org)
    create_case_A_objects(org)
    create_case_B_objects(org)
    create_case_C_objects(org)
    create_case_D_objects(org)
    
    return

def create_structure():
    # currently there is a duplicate data error if both cases are run
    # there are some notes below in create_cases about the nature of the 
    # problem but since currently only the all_cases is required what is
    # here works
    
    #create_individual_orgs()
    create_one_org_with_all_cases()

    return


def create_cycle(org):
    seed.models.Cycle.objects.get_or_create(name="2015 Annual",
                                                    organization = org,
                                                    start=datetime.datetime(2015,1,1),
                                                    end=datetime.datetime(2016,1,1)-datetime.timedelta(seconds=1))
    return


def create_cases(org, tax_lots, properties):
    cycle = seed.models.Cycle.objects.filter(organization=org).first()
    
    for (tl_def, prop_def) in itertools.product(tax_lots, properties):
        
        # Doesn't match
        # LINE 1: ...1'::date AND "bluesky_propertystate"."extra_data" = '{"Does ...
        # HINT:  No operator matches the given name and argument type(s). You might need to add explicit type casts.
        tax_extra_data = tax_lot_extra_data_map[tl_def["jurisdiction_taxlot_identifier"]]
        prop_extra_data = property_extra_data_map[prop_def["building_portfolio_manager_identifier"]]

        print "Adding {} prop extra datas.".format(prop_extra_data)

        # states don't have an org and since this script was doing all buildings twice 
        # (once for individual, once for _caseALL).  So if the get_or_create returns 
        # an existing one then it still is unknown if it is something that already exists.
        # Check the view model to see if there is something with this state and this org.
        # If it doesn't exist then create one.  If it does exist than that is correct (hopefully)
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

        for k in prop_extra_data:
            prop_state.extra_data[k] = prop_extra_data[k]

        prop_state.save()
         
        taxlot_state, taxlot_state_created = _create_state(seed.models.TaxLotView, 
                                                          seed.models.TaxLotState,                                                          
                                                          org,
                                                          tl_def)
        

        for k in tax_extra_data:
            taxlot_state.extra_data[k] = tax_extra_data[k]

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


        taxlot_view, created = seed.models.TaxLotView.objects.get_or_create(taxlot = taxlot, cycle=cycle, state = taxlot_state)
        prop_view, created = seed.models.PropertyView.objects.get_or_create(property=property, cycle=cycle, state = prop_state)

        tlp, created = seed.models.TaxLotProperty.objects.get_or_create(property_view = prop_view, taxlot_view = taxlot_view, cycle = cycle)

    return

def create_case_A_objects(org):
    tax_lots = [ {"jurisdiction_taxlot_identifier":"1552813",
                  "address": "050 Willow Ave SE",
                  "city": "Rust",
                  "number_properties": 1}]

    properties = [{ "building_portfolio_manager_identifier": 2264,
                    "property_name": "University Inn",
                    "address_line_1": "50 Willow Ave SE",
                    "city": "Rust",
                    "use_description": "Hotel",
                    "energy_score": 75,
                    "site_eui": 125,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area":12555,
                    "owner": "ULLC",
                    "owner_email": "ULLC@gmail.com",
                    "owner_telephone": "213-852-1238",
                    "property_notes": "Case A-1: 1 Property, 1 Tax Lot"}]

    create_cases(org, tax_lots, properties)
    return


def create_case_B_objects(org):

    tax_lots = [ {"jurisdiction_taxlot_identifier":"11160509",
                  "address": "2655 Welstone Ave NE",
                  "city": "Rust",
                  "number_properties": 2 }]


    properties = [{ "building_portfolio_manager_identifier": 3020139,
                    "property_name": "Hilltop Condos",
                    "address_line_1": "2655 Welstone Ave NE",
                    "city": "Rust",
                    "use_description": "Multi-family housing",
                    "energy_score": 1,
                    "site_eui": 652.3,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area":513852,
                    "owner": "Hilltop LLC",
                    "owner_email": "Hilltop@llc.com",
                    "owner_telephone": "426-512-4533",
                    "property_notes": "Case B-1: Multiple (3) Properties, 1 Tax Lot"},
                  { "building_portfolio_manager_identifier": 4828379,
                    "property_name": "Hilltop Condos",
                    "address_line_1": "2650 Welstone Ave NE",
                    "city": "Rust",
                    "use_description": "Office",
                    "energy_score": None,
                    "site_eui": None,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area":55121,
                    "owner": "Hilltop LLC",
                    "owner_email": "Hilltop@llc.com",
                    "owner_telephone": "213-859-8465",
                    "property_notes": "Case B-1: Multiple (3) Properties, 1 Tax Lot"},
                  { "building_portfolio_manager_identifier": 1154623,
                    "property_name": "Hilltop Condos",
                    "address_line_1": "2700 Welstone Ave NE",
                    "city": "Rust",
                    "use_description": "Retail",
                    "energy_score": 63,
                    "site_eui": 1202,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area":23543,
                    "owner": "Hilltop LLC",
                    "owner_email": "Hilltop@llc.com",
                    "owner_telephone": "213-546-9755",
                    "property_notes": "Case B-1: Multiple (3) Properties, 1 Tax Lot"}
    ]

    create_cases(org, tax_lots, properties)
    return



def create_case_C_objects(org):

    tax_lots = [ {"jurisdiction_taxlot_identifier":"33366555",
                  "address": "521 Elm Street",
                  "city": "Rust"},
                 {"jurisdiction_taxlot_identifier":"33366125",
                  "address": "525 Elm Street",
                  "city": "Rust"
                 },
                 {"jurisdiction_taxlot_identifier":"33366148",
                  "address": "530 Elm Street",
                  "city": "Rust"}]

    properties = [{ "building_portfolio_manager_identifier": 5233255,
                    "property_name": "Montessori Day School",
                    "address_line_1": "512 Elm Street",
                    "city": "Rust",
                    "use_description": "K-12 School",
                    "energy_score": 55,
                    "site_eui": 1358,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area": "20000",
                    "owner": "Norton Schools",
                    "owner_email": "Lee@norton.com",
                    "owner_telephone": "213-555-4368",
                    "property_notes": "Case C: 1 Property, Multiple (3) Tax Lots"}]

    create_cases(org, tax_lots, properties)
    return


def create_case_D_objects(org):

    tax_lots = [ {"jurisdiction_taxlot_identifier":"24651456",
                  "address": "11 Ninth Street",
                  "city": "Rust",
                  "number_properties": 5
                  },
                 {"jurisdiction_taxlot_identifier":"13334485",
                  "address": "93029 Wellington Blvd",
                  "city": "Rust",
                  "number_properties": None,
                 },
                 {"jurisdiction_taxlot_identifier":"23810533",
                  "address": "94000 Wellington Blvd",
                  "city": "Rust",
                  "number_properties": None,
                 }]

    campus = [{ "building_portfolio_manager_identifier": 1311523,
                "pm_parent_property_id" : 1311523,
                "property_name": "Lucky University ",
                "address_line_1": "11 Ninth Street",
                "city": "Rust",
                "use_description": "College/University",
                "energy_score": None,
                "site_eui": None,
                "year_ending": datetime.datetime(2015,12,31),
                "gross_floor_area": None,
                "owner": "Lucky University",
                "owner_email": "ralph@lucky.edu",
                "owner_telephone": "224-587-5602",
                "property_notes": "Case D: Campus with Multiple associated buildings"}]

    properties = [
        { "building_portfolio_manager_identifier": 1311524,
         "pm_parent_property_id" : 1311523,
          "property_name": "Grange Hall ",
          "address_line_1": "12 Ninth Street",
          "city": "Rust",
          "use_description": "Performing Arts",
          "energy_score": 77,
          "site_eui": 219,
          "year_ending": datetime.datetime(2015,12,31),
          "gross_floor_area": 124523,
          "owner": "Lucky University",
          "owner_email": "ralph@lucky.edu",
          "owner_telephone": "224-587-5602",
          "property_notes": "Case D: Campus with Multiple associated buildings"},
        { "building_portfolio_manager_identifier": 1311525,
         "pm_parent_property_id" : 1311523,
          "property_name": "Biology Hall ",
          "address_line_1": "20 Tenth Street",
          "city": "Rust",
          "use_description": "Laboratory",
          "energy_score": 43,
          "site_eui": 84,
          "year_ending": datetime.datetime(2015,12,31),
          "gross_floor_area": 421351,
          "owner": "Lucky University",
          "owner_email": "ralph@lucky.edu",
          "owner_telephone": "224-587-5602",
          "property_notes": "Case D: Campus with Multiple associated buildings"},

                  { "building_portfolio_manager_identifier": 1311526,
                   "pm_parent_property_id" : 1311523,
                    "property_name": "Rowling Gym ",
                    "address_line_1": "35 Tenth Street",
                    "city": "Rust",
                    "use_description": "Fitness Center/Health Club/Gym",
                    "energy_score": 59,
                    "site_eui": 72,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area": 1234,
                    "owner": "Lucky University",
                    "owner_email": "ralph@lucky.edu",
                    "owner_telephone": "224-587-5602",
                    "property_notes": "Case D: Campus with Multiple associated buildings"},

                  { "building_portfolio_manager_identifier": 1311527,
                   "pm_parent_property_id" : 1311523,
                    "property_name": "East Computing Hall ",
                    "address_line_1": "93029 Wellington Blvd",
                    "city": "Rust",
                    "use_description": "College/University",
                    "energy_score": 34,
                    "site_eui": 45,
                    "year_ending": datetime.datetime(2015,12,31),
                    "gross_floor_area": 45324,
                    "owner": "Lucky University",
                    "owner_email": "ralph@lucky.edu",
                    "owner_telephone": "224-587-5602",
                    "property_notes": "Case D: Campus with Multiple associated buildings"},
        { "building_portfolio_manager_identifier": 1311528,
         "pm_parent_property_id" : 1311523,
          "property_name": "International House",
          "address_line_1": "93029 Wellington Blvd",
          "city": "Rust",
          "use_description": "Residence",
          "energy_score": None,
          "site_eui": None,
          "year_ending": datetime.datetime(2015,12,31),
          "gross_floor_area": 482215,
          "owner": "Lucky University",
          "owner_email": "ralph@lucky.edu",
          "owner_telephone": "224-587-5602",
          "property_notes": "Case D: Campus with Multiple associated buildings"}]

    # I manually create everything here
    cycle = seed.models.Cycle.objects.filter(organization=org).first()
        
    def add_extra_data(state, extra_data):
        if not extra_data:
            return state
        
        for k in extra_data:
            state.extra_data[k] = extra_data[k]
        state.save()
        return state

    campus_property, __ = seed.models.Property.objects.get_or_create(organization=org, campus=True)
    property_objs  = [seed.models.Property.objects.create(organization=org, parent_property=campus_property) for p in properties]

    property_objs.insert(0, campus_property)
    taxlot_objs = [seed.models.TaxLot.objects.create(organization=org) for t in tax_lots]

    property_states = [seed.models.PropertyState.objects.get_or_create(**prop_def)[0] for prop_def in itertools.chain(campus, properties)]
    property_states = [add_extra_data(ps, property_extra_data_map.get(ps.building_portfolio_manager_identifier)) for ps in property_states]
    
    property_views = [seed.models.PropertyView.objects.get_or_create(property=property, cycle=cycle, state = prop_state)[0] for (property, prop_state) in zip(property_objs, property_states)]

    taxlot_states = [seed.models.TaxLotState.objects.get_or_create(**lot_def)[0] for lot_def in tax_lots]
    taxlot_states = [add_extra_data(tls, tax_lot_extra_data_map.get(tls.jurisdiction_taxlot_identifier)) for tls in taxlot_states]
    
    taxlot_views = [seed.models.TaxLotView.objects.get_or_create(taxlot=taxlot, cycle=cycle, state = taxlot_state)[0] for (taxlot, taxlot_state) in zip(taxlot_objs, taxlot_states)]

    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[0], taxlot_view = taxlot_views[0], cycle = cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[1], taxlot_view = taxlot_views[0], cycle = cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[2], taxlot_view = taxlot_views[0], cycle = cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[3], taxlot_view = taxlot_views[0], cycle = cycle)

    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[4], taxlot_view = taxlot_views[1], cycle = cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[4], taxlot_view = taxlot_views[2], cycle = cycle)

    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[5], taxlot_view = taxlot_views[1], cycle = cycle)
    seed.models.TaxLotProperty.objects.get_or_create(property_view = property_views[5], taxlot_view = taxlot_views[2], cycle = cycle)

    return



class Command(BaseCommand):
    def handle(self, *args, **options):
        create_structure()
        return
