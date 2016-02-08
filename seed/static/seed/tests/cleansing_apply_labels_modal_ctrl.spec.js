describe("controller: cleansing_apply_labels_modal_ctrl", function(){

	var mock_label_service, scope, modal_state;
	var ctrl, ctrl_scope, modalInstance, timeout;
	
	beforeEach(function() {
        module('BE.seed');
    });

	beforeEach(inject(function($controller, $rootScope, $uibModal, $q, label_service){
		ctrl = $controller;
		scope = $rootScope;
        ctrl_scope = $rootScope.$new();        
        modal_state = "";

        mock_label_service = label_service;
        spyOn(mock_label_service, "apply_cleansing_labels")
        	.andCallFake(function(){        		
                // return $q.reject for error scenario
                return $q.when({"status": "success"});
        	});
	}));

	// this is outside the beforeEach so it can be configured by each unit test
	function create_cleansing_apply_labels_modal_controller(){

		var mock_error_labels = [
			{ 
				id: 1,
			  	name: "error label 1",
			  	text: "error label 1",
			  	label: "danger",
			  	color: "red"
			},
			{ 
				id: 2,
			 	name: "error label 2",
			  	text: "error label 2",
			  	label: "danger",
			  	color: "red"
			}			
		];

		var mock_cleansing_results = [
			{
				building_id : 1,
				cleansingResults: [
					{
						message : "error 1"
					}
				]
			},
			{
				building_id : 2,
				cleansingResults: [
					{
						message : "error 1"
					},
					{
						message : "error 2"
					}
				]
			},
		];


		ctrl = ctrl('cleansing_apply_labels_modal_ctrl', {
			$scope : ctrl_scope,
			$uibModalInstance : {
				close: function() {
                    modal_state = "close";
                },
                dismiss: function() {
                    modal_state = "dismiss";
                }
			},
			errorLabels: mock_error_labels,
			cleansingResults: mock_cleansing_results,
			label_service : mock_label_service
		});
	}


	 it("should close the modal when the done function is called", function() {
        // arrange
        create_cleansing_apply_labels_modal_controller();

        // act
        ctrl_scope.done();
        ctrl_scope.$digest();

        // assertions
        expect(modal_state).toBe("close");
    });

    it("should cancel the modal when the cancel function is called", function() {
        // arrange
        create_cleansing_apply_labels_modal_controller();

        // act
        ctrl_scope.cancel();
        ctrl_scope.$digest();

        // assertions
        expect(modal_state).toBe("dismiss");
    });


});