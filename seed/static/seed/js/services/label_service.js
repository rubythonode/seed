angular.module('BE.seed.service.label', 
    []).factory('label_service', [ '$http',
                                    '$q',
                                    '$timeout',
                                    '$log',
                                    'user_service',
                                    'label_helper_service',
                                    'urls',
                        function (  $http, 
                                    $q, 
                                    $timeout,
                                    $log,
                                    user_service,
                                    label_helper_service,
                                    urls
                                    ) {


    /** Label Service:  
        --------------------------------------------------
        Provides methods to CRUD labels on the server
        as well as apply and remove labels to buildings.

        Note: This is the first service to use proper REST verbs and REST-based 
        server APIs (provided by django-rest-framework).
        If this approach works well, the hope is to refactor all Angular services
        to use REST verbs and APIs.
    */


    /** Returns an array of labels.
    
        @param {array} selected_buildings       An array of building ids corresponding to 
                                                selected buildings (should be empty if 
                                                select_all_checkbox is true).
        @param {boolean} select_all_checkbox    A boolean indicating whether user checked 
                                                'Select all' checkbox.
        @param {object} search_params           A reference to the Search object, which 
                                                includes properties for active filters.

        Returned label objects should have the following properties, 
        with 'text' and 'color' properties assigned locally.
        
            id {integer}            The id of the label.
            name {string}           The text that appears in the label.
            text {string}           Same as name, needed for ngTagsInput control.
            color {string}          The text description of the label's color (e.g. 'blue').
            label {string}          The css class, usually in bootstrap, used to generate
                                    the color style (poorly named, needs refactoring).
            is_applied {boolean}    If a search object was passed in, this boolean 
                                    indicates if buildings in the current filtered 
                                    set have this label.

        For example...
        [
            {                
                id: 1,                
                name: "test1",
                color: "blue",
                label: "primary",
                text: "test1",
                is_applied : true
            }
        ]
    */
    
    function get_labels(selected_buildings, select_all_checkbox, search_params) {
        var defer = $q.defer();
       
        var searchArgs = _.extend({
            'selected_buildings' : selected_buildings,
            'select_all_checkbox' : select_all_checkbox,
             organization_id: user_service.get_organization().id
        }, search_params);
       
        $http({
            method: 'GET',
            url: window.BE.urls.label_list,
            params: searchArgs
        }).success(function(data, status, headers, config) {
            
            if (_.isEmpty(data.results)) {
                data.results = [];
            }

            data.results = _.map(data.results, update_label_w_local_props);
            defer.resolve(data);

        }).error(function(data, status, headers, config) {
            defer.reject(data, status);
        });
        return defer.promise;
    }


    /*  Add a label to an organization's list of labels 

        @param {object} label       Label object to use for creating label on server.
                                   
        @return {object}            Returns a promise object which will resolve
                                    with either a success if the label was created
                                    on the server, or an error if the label could not be
                                    created on the server. 

                                    Return object should also have a 'label' property assigned 
                                    to the newly created label object.
    */
    function create_label(label){
        var defer = $q.defer();
        $http({
            method: 'POST',
            'url': window.BE.urls.label_list,
            'data': label,
            'params': {
                'organization_id': user_service.get_organization().id
            }
        }).success(function(data, status, headers, config) {
            if(data){
                data = update_label_w_local_props(data);
            }            
            defer.resolve(data);
        }).error(function(data, status, headers, config) {
            defer.reject(data, status);
        });
        return defer.promise;
    }


    /*  Update an existing a label in an organization 
        
        @param {object} label   A label object with changed properties to update on server.
                                The object must include property 'id' for label ID. 

        @return {object}        Returns a promise object which will resolve
                                with either a success if the label was updated, 
                                or an error if not.                             
                                Return object will have a 'label' property assigned 
                                to the updated label object.
    */
    function update_label(label){
        var defer = $q.defer();
        $http({
            method: 'PUT',
            'url': window.BE.urls.label_list + label.id + '/',
            'data': label,
            'params': {
                'organization_id': user_service.get_organization().id
            }
        }).success(function(data, status, headers, config) {
            if(data){
                data = update_label_w_local_props(data);
            }  
            defer.resolve(data);
        }).error(function(data, status, headers, config) {
            defer.reject(data, status);
        });
        return defer.promise;
    }

    /*  Delete a label from the set of labels for an organization.

        @param {object} label       Label object to delete on server.
                                    Must include property 'id' for label ID. 

        @return {object}            Returns a promise object which will resolve
                                    with either a success if the label was deleted, 
                                    or an error if not.
    */
    function delete_label(label){
        var defer = $q.defer();
        $http({
            method: 'DELETE',
            'url': window.BE.urls.label_list + label.id + '/',
            'params': {
                'organization_id': user_service.get_organization().id
            }
        }).success(function(data, status, headers, config) {
            defer.resolve(data);
        }).error(function(data, status, headers, config) {
            defer.reject(data, status);
        });
        return defer.promise;
    }


    /* FUNCTIONS FOR LABELS WITHIN BUIDINGS  */
    /* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~*/

    /*  

    This method updates selected buildings with a group of "add" labels
    and a group of "remove" labels. 

    
    @param {array} add_label_ids            An array of label ids to apply to selected buildings.
    @param {array} remove_label_ids         An array of label ids to remove from selected buildings.
    @param {array} selected_buildings       An array of building ids corresponding to selected buildings
                                            (should be empty if select_all_checkbox is true).
    @param {boolean} select_all_checkbox    A boolean indicating whether user checked 'Select all' checkbox.
    @param {object} search_params           A reference to the Search object, which includes
                                            properties for active filters.

    @return {object}                        A promise object that resolves server response
                                            (success or error).

    */
    function update_building_labels(add_label_ids, remove_label_ids, selected_buildings, select_all_checkbox, search_params) {
        var defer = $q.defer();
        $http({
            method: 'PUT',
            'url': window.BE.urls.update_building_labels,
            'params': _.extend({
                'selected_buildings' : selected_buildings,
                'select_all_checkbox': select_all_checkbox,
                'organization_id': user_service.get_organization().id
            }, search_params),
            'data': {
                'add_label_ids': add_label_ids,
                'remove_label_ids': remove_label_ids
            }
        }).success(function(data, status, headers, config) {
            defer.resolve(data);
        }).error(function(data, status, headers, config) {
            defer.reject(data, status);
        });
        return defer.promise;
    }


    /* 

    This method applies labels to sets of buildings as part of the data cleansing process. 
    TODO: At some point this method should be made more generic, so that it's not coupled directly
    to data cleansing (semantically or otherwise) and allows removing labels from buildings.
    
    @param {array} apply_label_objs     An array of objects, each of which defines a label id and an array
                                        of buildings to apply that label to.

    Each apply_label_obj in apply_label_objs should have the following structure:

        For existing labels...
        { 
            label_id :1,                                //The label's id
            add_to_building_ids : [1,2,3],              //An array of building ids to apply label to
        }

        For new labels...
        {            
            label_id: null,                     //null means this is a new label
            label_name: "new label",
            label_color: "red",
            add_to_building_ids : [1,4]         //An array of building IDs to apply label to after creation 
        }

    Note that building ids should point to 'canonical' building snapshot rows.

    */

    function apply_cleansing_building_labels(apply_label_objs) {

        //VALIDATE ARGUMENTS
        //A bit defensive coding : let's test to make sure 
        //the argument is properly formed and throw an error if not.
        if (!angular.isDefined(apply_label_objs) || !angular.isArray(apply_label_objs) || apply_label_objs.length===0){
            throw "Invalid argument. apply_label_objs must be an array with one or more elements.";
        }
        _.each(apply_label_objs, function(apply_label_obj){
            if (!angular.isNumber(apply_label_obj.label_id) && apply_label_obj.label_id!==null){
                throw "Invalid property: label_id must be an integer or 'null'";
            }          
            if (!angular.isDefined(apply_label_obj.add_to_building_ids) || 
                !angular.isArray(apply_label_obj.add_to_building_ids) || 
                apply_label_obj.add_to_building_ids.length===0){
                throw "Invalid argument. add_to_building_ids must be an array with one or more elements.";
            }  
            //if id is null, the new label properties should be defined
            if (apply_label_obj.label_id===null){                
                if (!angular.isDefined(apply_label_obj.label_name)){
                    throw "Invalid property: label_name must be defined";
                }
                if (!angular.isDefined(apply_label_obj.label_color)){
                    throw "Invalid property: label_color must be defined";
                }
            }
        });
        
        //BUILD EXTRA PROPERTIES FOR CALL
        //Because of the way django-rest works, we have to build two extra properties for the server.
        //These properties indicate which labels and buildings are involved in the apply operation
        var label_ids = _(apply_label_objs).chain().pluck('label_id').uniq().compact().value();  
        var building_ids = _(apply_label_objs).chain().pluck('add_to_building_ids').flatten().union().uniq().value();

        //MAKE SERVER CALL        
        var defer = $q.defer();
        $http({
            method: 'PUT',
            'url': window.BE.urls.cleansing_building_labels,
            'data': {
                'building_ids': building_ids,
                'label_ids': label_ids,
                'updates': apply_label_objs
            },
            'params': {
                'organization_id': user_service.get_organization().id
            }
        }).success(function(data, status, headers, config) {
            defer.resolve(data);
        }).error(function(data, status, headers, config) {
            defer.reject(data, status);
        });
        return defer.promise;
    }

    /*  Gets the list of supported colors for labels, based on default bootstrap
        styles for labels. These are defined locally.

        @return {array}     List of label option objects.

        Label option objects have the following structure
        {
            'label' : {string} name of bootstrap class for label
            'color' : {string} text description of color
        }

        NOTE: At some point label colors should be defined on the server and not 
        directly related to bootstrap colors. If we do stay with Bootstrap colors
        we should change the property names to something like 'bootstrap-class' and 
        'color-description' (rather than 'label') to make them more clear.

    */
    function get_available_colors() {
        return [
            {
                'label': 'success',
                'color': 'green'
            },
            {
                'label': 'danger',
                'color': 'red'
            },
            {
                'label': 'default',
                'color': 'gray'
            },
            {
                'label': 'warning',
                'color': 'orange'
            },
            {
                'label': 'info',
                'color': 'light blue'
            },
            {
                'label': 'primary',
                'color': 'blue'
            }
        ];
    }

    /* Check if color string is a valid color */
    function is_valid_color(color){
        var colorsArr = get_available_colors();
        return _.contains(_.pluck(colorsArr, "color"), color);
    }

    /*  Add a few properties to the label object so that it
        works well with UI components.
    */
    function update_label_w_local_props(lbl){
        // add bootstrap label class names
        lbl.label = label_helper_service.lookup_label(lbl.color);
        // create 'text' property needed for ngTagsInput control
        lbl.text = lbl.name;
        return lbl;
    }


    /*  Create a temporary label as a placeholder on the front
        end during user action that may ultimately create
        a label on the back en.. */

    function create_temp_label(temp_name, temp_color){

        if (!temp_color || !is_valid_color(temp_color)){
            console.log("Invalid color argument '" + temp_color + "' ') in create_temp_label. Defaulting to red.");
            temp_color = "red";
        }
        if (!temp_name){
            temp_name = "Unnamed";
        }        

        //An id of null indicates its a temporary label  
        var temp_label = {                
            id: null,                             
            name: temp_name,
            color: temp_color,
            label: label_helper_service.lookup_label(temp_color),
            text: temp_name,
            is_applied : false
        };

        return temp_label;
    }

    /* Public API */

    var label_factory = { 
        
        //functions
        get_labels : get_labels ,
        create_label : create_label,
        update_label : update_label,
        delete_label : delete_label,
        update_building_labels : update_building_labels,
        apply_cleansing_building_labels: apply_cleansing_building_labels,
        get_available_colors : get_available_colors,
        create_temp_label : create_temp_label,
    
    };

    return label_factory;

}]);
