/*
 * :copyright (c) 2014 - 2015, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.
 * :author
 */
angular.module('BE.seed.controller.cleansing_apply_labels_modal_ctrl', [])
.controller('cleansing_apply_labels_modal_ctrl', [
  '$scope',
  '$uibModalInstance',
  'errorLabels',
  'cleansingResults',
  'label_service',
  function(
    $scope,
    $uibModalInstance,
    errorLabels,
    cleansingResults,
    label_service
    ){


    /* DEFINE SCOPE AND LOCAL VARS  */
    /* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */   

    //make sure each incoming error label is set to unchecked
    _.each(errorLabels, function(label){
        label.is_checked_add = false;
    });

     /* View status */
    $scope.STATUS_READY = "ready";
    $scope.STATUS_COMPLETE = "complete";
    $scope.status = $scope.STATUS_READY;

    // A string to describe server error to user, null if there is no error.
    $scope.apply_labels_error = null;

    // A list of labels for cleansing errors in this data set.
    // Note that some labels might be 'temporary' with an id of null,
    // since they haven't been created on the server yet. 
    $scope.errorLabels = errorLabels;
    
    // cleansingResults array: this is an array of objects that include 
    // a building "id" property and a "cleansingResults" child array.
    // This child "cleansingResults" array contains one or more 
    // objects describing the error row, including an error "message" property.
    // In this controller, we're only concerned with the parent object "id" property 
    // the child object "message" properties.
    $scope.cleansingResults = cleansingResults;

    // Bind for view
    $scope.num_labels_applied = 0;

    // At least one apply button checked 
    $scope.is_checked = false;


    /* HANDLE UI INTERACTIONS */
    /* ~~~~~~~~~~~~~~~~~~~~~~ */   

    /*  User has selected 'Cancel' on modal,
        so don't apply any labels */
    $scope.cancel = function (){
    	$uibModalInstance.dismiss('cancel');
    };

    /* User has clicked 'Done' button after applying labels */
    $scope.done = function() {
        $uibModalInstance.close();    
    };

    /* User has clicked an 'Select' row button */
    $scope.on_select_change = function(){
       $scope.is_checked = _.some($scope.errorLabels, function(label){
            return label.is_checked_add === true;
       });
    };

    /*  Use has clicked 'Apply Now' on modal, which means
        apply all error labels they have selected */
    $scope.apply_now = function() {

        //reset state vars
        $scope.status = $scope.STATUS_READY;
        $scope.apply_labels_error = null;

        //gather data for service call
        var selected_labels = _.filter(errorLabels, function(label){
            return label.is_checked_add===true;
        });
        var bulk_apply_labels_data = build_bulk_apply_labels_data(selected_labels, $scope.cleansingResults);

        //remember how many labels we're updating
        $scope.num_labels_applied = selected_labels.length;

        //TODO: show progress

        //do service call
        label_service.apply_cleansing_building_labels(bulk_apply_labels_data).then(
            function(data){
                //labels were applied successfully
                $scope.status = $scope.STATUS_COMPLETE;                
            },
            function(data, status) {
                // Rejected promise, error occurred.
                // TODO: Make this nicer...just doing alert for development
                $scope.apply_labels_error = "Error applying labels.";
                $scope.status = $scope.STATUS_READY;  
            }       	
        );
    };



    /* 'PRIVATE' HELPER FUNCTIONS */
    /* ~~~~~~~~~~~~~~~~~~~~~~~~~~ */   


    /*  Build an array of objects, each defining a label to be applied to a set of buildings

        @param  selected_labels     a set of label objects 
        @param  cleansingResults    a 'cleansingResults' object, which contains an array of objects,
                                    each with a cleansing_results array that contains an array of errors
                                    for that row.

        @returns  array             returns an array of 'bulk label update' data. See service for object defintion.
                                    TODO: This may warrant a defined value object to formalize properties.


                                    

     */
    function build_bulk_apply_labels_data(selected_labels, cleansingResults){

        var bulk_apply_labels_data = [];
        
        _.each(selected_labels, function(label){
             
            var update_label_data = {
                label_id: label.id,
                add_to_building_ids: []
            };
                         
            // If the current label's name appears at least once as an error 'message' 
            // in a building's set of error rows, we'll apply the label to that building id.
            _.each(cleansingResults, function(cleansingResult){   
                var error_exists = _.findWhere(cleansingResult.cleansing_results, {message: label.name});
                if (error_exists){                    
                    update_label_data.add_to_building_ids.push(cleansingResult.id);
                }
            });

            //assign defaults for a new label created during data cleansing
            if (label.id===null){
                update_label_data.label_name = label.name;                 
                update_label_data.label_color = "red";
            }

            bulk_apply_labels_data.push( update_label_data );
        
        });


        return bulk_apply_labels_data;
                
    }

   



}]);
