/*
 * :copyright (c) 2014 - 2016, The Regents of the University of California, through Lawrence Berkeley National Laboratory (subject to receipt of any required approvals from the U.S. Department of Energy) and contributors. All rights reserved.
 * :author
 */
angular.module('BE.seed.controller.cleansing', [])
.controller('cleansing_controller', [
  '$scope',
  '$uibModalInstance',
  '$uibModal',
  'search_service',
  'cleansingResults',
  'label_service',
  'name',
  'uploaded',
  'importFileId',
  'urls',
  function(
    $scope,
    $uibModalInstance,
    $uibModal,
    search_service,
    cleansingResults,
    label_service,
    name,
    uploaded,
    importFileId,
    urls
  ) {


    var fields = [];
    var columns = [];

    /* HANDLE UI INTERACTIONS */
    /* ~~~~~~~~~~~~~~~~~~~~~~ */   
    
    /*  Show modal to allow user to select subset of error labels 
        from all errors shown.*/
    $scope.show_apply_labels_modal = function (){
     
      var applyLabelModalInstance = $uibModal.open(
        {
          templateUrl: urls.static_url + 'seed/partials/cleansing_apply_labels_modal.html',
          controller: 'cleansing_apply_labels_modal_ctrl',
          resolve: {
              errorLabels : function() {
                return $scope.errorLabels;
              },
              cleansingResults : function() {
                return $scope.cleansingResults;
              }
          }
        }
      );

      applyLabelModalInstance.result.then(
            function () {
              //dialog was closed with 'Done' button. Right now nothing to do but perhaps later
              //we want to show some kind of 'num buildings updated' label in this view.
            }, 
            function (message) {
               //dialog was 'dismissed,' which means it was cancelled...so nothing to do. 
            }
        );

    };


    /* Handle 'Close' button click for this cleansing modal */
    $scope.close = function () {
      $uibModalInstance.close();
    };

    /* Handle user interactions with sort fields (called on enter key) */
    $scope.sortData = function() {
      $scope.cleansingResults = _.sortByOrder($scope.cleansingResults, [$scope.search.sort_column], [$scope.search.sort_reverse ? 'desc' : 'asc']);
    };



    /* HELPER FUNCTIONS */
    /* ~~~~~~~~~~~~~~~~ */

    /* Override the search objects storage, search and filter functions */

    function setup_local_search_overrides(){

      $scope.search.init_storage = function (prefix) {
        // Check session storage for order and sort values.
        if (typeof(Storage) !== "undefined") {
          $scope.search.prefix = prefix;

          // order_by & sort_column
          if (sessionStorage.getItem(prefix + ':' + 'seedBuildingOrderBy') !== null) {
            $scope.search.order_by = sessionStorage.getItem(prefix + ':' + 'seedBuildingOrderBy');
            $scope.search.sort_column = sessionStorage.getItem(prefix + ':' + 'seedBuildingOrderBy');
          }

          // sort_reverse
          if (sessionStorage.getItem(prefix + ':' + 'seedBuildingSortReverse') !== null) {
            $scope.search.sort_reverse = JSON.parse(sessionStorage.getItem(prefix + ':' + 'seedBuildingSortReverse'));
          }

          // filter_params
          if (sessionStorage.getItem(prefix + ':' + 'seedBuildingFilterParams') !== null) {
            $scope.search.filter_params = JSON.parse(sessionStorage.getItem(prefix + ':' + 'seedBuildingFilterParams'));
          }

          // number_per_page
          if (sessionStorage.getItem(prefix + ':' + 'seedBuildingNumberPerPage') !== null) {
            $scope.search.number_per_page = $scope.search.number_per_page_options_model = $scope.search.showing.end =
              JSON.parse(sessionStorage.getItem(prefix + ':' + 'seedBuildingNumberPerPage'));
          }
        }
      };
      $scope.search.column_prototype.toggle_sort = function () {
        if (this.sortable) {
          if ($scope.search.sort_column === this.sort_column) {
            $scope.search.sort_reverse = !$scope.search.sort_reverse;
          } else {
            $scope.search.sort_reverse = true;
            $scope.search.sort_column = this.sort_column;
          }

          if (typeof(Storage) !== "undefined") {
            sessionStorage.setItem($scope.search.prefix + ':' + 'seedBuildingOrderBy', $scope.search.sort_column);
            sessionStorage.setItem($scope.search.prefix + ':' + 'seedBuildingSortReverse', $scope.search.sort_reverse);
          }

          $scope.search.order_by = this.sort_column;
          $scope.sortData();
        }
      };
      $scope.search.column_prototype.sorted_class = function () {
        if ($scope.search.sort_column === this.sort_column) {
          if ($scope.search.sort_reverse) {
            return "sorted sort_asc";
          } else {
            return "sorted sort_desc";
          }
        } else {
          return "";
        }
      };
      $scope.search.filter_search = function () {
        $scope.search.sanitize_params();
        _.each($scope.cleansingResults, function (result) {
          if (!result.visible) result.visible = true;
          _.each(result.cleansing_results, function(row) {
            if (!row.visible) row.visible = true;
          });
        });
        _.each(this.filter_params, function(value, column) {
          value = value.toLowerCase();
          _.each($scope.cleansingResults, function (result) {
            if (result.visible) {
              if (_.contains(['field', 'message'], column)) {
                _.each(result.cleansing_results, function(row) {
                  if (!_.contains(row[column].toLowerCase(), value)) row.visible = false;
                });
              } else {
                if (_.isNull(result[column]) || !_.contains(result[column].toLowerCase(), value)) result.visible = false;
              }
            }
          });
        });
        if (typeof(Storage) !== "undefined") {
          sessionStorage.setItem(this.prefix + ':' + 'seedBuildingFilterParams', JSON.stringify(this.filter_params));
        }
      };
    }



    /* In the data cleansing modal we only show a 
       specific subset of columns for the data.
       Define those fields and columns here. */

    function init_fields_and_columns(){

      fields = [{
        sort_column: 'address_line_1',
        sortable: true,
        title: 'Address Line 1'
      }, {
        sort_column: 'pm_property_id',
        sortable: true,
        title: 'PM Property ID'
      }, {
        sort_column: 'tax_lot_id',
        sortable: true,
        title: 'Tax Lot ID'
      }, {
        sort_column: 'custom_id_1',
        sortable: true,
        title: 'Custom ID'
      }, {
        sort_column: 'field',
        sortable: false,
        title: 'Field'
      }, {
        sort_column: 'message',
        sortable: false,
        title: 'Error Message'
      }];
        
      columns = _.pluck(fields, 'sort_column');
      _.each(fields, function(field) {
        field.checked = false;
        field.class = 'is_aligned_right';
        field.field_type = null;
        field.link = false;
        field.static = false;
        field.type = 'string';
      });

    }

    /* Take a cleansing results object and return a  array of unique error messages */
    function get_unique_error_messages(cleansingResults){
      return _($scope.cleansingResults).chain().pluck('cleansing_results').flatten().pluck('message').unique().value();
    }

    /* Take a list of cleansing error strings and build an array of labels.
       User the provided set of existing labels and create 'temporary'
       labels (with no id) for the remaining cleansing error messages without matching labels. */
    function create_error_labels(uniqueErrorMessagesArr, existingLabelsArr){

      var allErrorLabels = angular.copy(existingLabelsArr);

      //Assign local label properties to labels that have an id. 
      //This usually happens during a label_service call (and should be internal to label_service)
      //but in this controller, the labels come in directly with cleansing results
      //so we have to assign local label properties manually.
      _.each(allErrorLabels, function(label){
        if (angular.isNumber(label.id)){
          label_service.update_label_w_local_props(label);
        }
      });      
      
      //Create 'temporary' labels for error messages in cleansing
      //that don't have an existing label.   
      _.each(uniqueErrorMessagesArr, function (errorMessage){
        if (_.findWhere(existingLabelsArr, {name: errorMessage})===undefined){
          var newTempLabel = label_service.create_temp_label(errorMessage, 'red');
          allErrorLabels.push(newTempLabel);
        } 
      });

      return allErrorLabels;
    }
   
    /* INIT SCOPE, LOCAL PROPERTIES AND SEARCH */
    /* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
    
    $scope.name = name;
    $scope.uploaded = moment.utc(uploaded).local().format('MMMM Do YYYY, h:mm:ss A Z');
    $scope.cleansingResults = cleansingResults.cleansing_results;
    $scope.importFileId = importFileId;

    //Build an array of 'error' labels, creating temporary labels
    //for those that do not exist yet.
    var uniqueErrorMessages = get_unique_error_messages(cleansingResults.cleansing_results);
    $scope.errorLabels = create_error_labels(uniqueErrorMessages, cleansingResults.labels);

    // Setup local props for grid
    init_fields_and_columns();

    //Setup search    
    $scope.search = angular.copy(search_service);
    $scope.search.num_pages = 1;
    $scope.search.number_per_page = $scope.cleansingResults.length;
    $scope.search.sort_column = null;
    setup_local_search_overrides();

    //Generate columns for view
    $scope.columns = $scope.search.generate_columns(
      fields,
      columns,
      $scope.search.column_prototype
    );

    //Init search
    $scope.search.init_storage('cleansing');
    if ($scope.search.sort_column !== null) $scope.sortData();
    $scope.search.filter_search();

    

   
}]);
