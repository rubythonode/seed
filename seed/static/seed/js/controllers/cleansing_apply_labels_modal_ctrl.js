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

    // keep track of process of applying labels
    $scope.apply_labels_complete = false;

    // A string to describe server error to user, null if there is no error.
    $scope.apply_labels_error = null;

    // A list of labels for cleansing errors in this data set.
    // Note that some labels might be 'temporary' as they haven't
    // been created on the server yet. 
    $scope.errorLabels = errorLabels;
    
    // cleansingResults array: this is an array of objects with a building "id" property 
    // and a "cleansingResults" child array.
    // This child "cleansingResults" array contains one or more objects describing the error row, 
    // including an error "message" property.
    // In this controller, we're only concerned with these "id" and "message" properties.
    $scope.cleansingResults = cleansingResults;

    // Var for view
    $scope.num_labels_applied = 0;

    /* At least one apply button checked */
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

        $scope.apply_labels_complete = false;
        $scope.apply_labels_error = null;

        //Get data in right format for service
        var selected_labels = _.filter(errorLabels, function(label){
            return label.is_checked_add===true;
        });
        var label_ids = _.pluck(selected_labels, 'id');
        var bulk_updates = build_bulk_update_labels_data(selected_labels, $scope.cleansingResults);

        // TODO need building ids here.
        var building_ids = [];

        //save number of labels for complete message
        $scope.num_labels_applied = label_ids.length;

        //TODO: show progress

        //do call
        label_service.cleansing_building_labels(label_ids, building_ids, bulk_updates).then(
            function(data){
                //if labels were applied successfully, 
                //switch mode of modal to show success message and 'done'
                $scope.apply_labels_complete = true;                
            },
            function(data, status) {
                // Rejected promise, error occurred.
                // TODO: Make this nicer...just doing alert for development
                alert('Error updating building labels: ' + status.toString());
                $scope.apply_labels_error = "Error applying labels (" + status.toString() + ")";
            }       	
        );
    };



    /* 'PRIVATE' HELPER FUNCTIONS */
    /* ~~~~~~~~~~~~~~~~~~~~~~~~~~ */   


    /* Build an array of objects defining labels and the buildings they should be applied to */
    function build_bulk_update_labels_data(selected_labels, cleansingResults){

        var bulk_update_labels_data = [];
        
        _.each(selected_labels, function(label){
             
            var update_label_data = {
                label_id: label.id,
                building_ids: []
            };

            //collect all building ids this label should be applied to
            _.each(cleansingResults, function(cleansingResult){
                if (_.findWhere(cleansingResult.cleansing_results, {message: label.name})){
                    update_label_data.building_ids.push(cleansingResult.id);
                }
            });

            //assign defaults for a new label created during data cleansing
            if (update_label_data.label_id===null){
                update_label.label_name = label.name;                 
                update_label_data.color = "red";
                update_label_data.label = "danger";
            }

            bulk_update_labels_data.push( update_label_data );
        
        });

        return bulk_update_labels_data;
    }

   



}]);
