Feature: The user can change the name of an appliance. The appliance is just renamed, all information is still there,
  i.e. the watt and its status. The appliance keeps its history of power consumption measurements, too.

  Scenario: The user can change the name of an appliance and is redirected to the new page where the name has changed.
    Given the user goes to the appliance configuration page of the Washing machine
    When they change the name to Machine making dirty clothes clean again
    And they submit the form
    Then they see a success message
    And they are on the appliance configuration page of Machine making dirty clothes clean again
    And the main headline contains Machine making dirty clothes clean again

  Scenario: There is an appliance with a longer history. When renaming this appliance, the history is still there.
    Given 40000 power consumptions are created for the Toploader spread over the last 14 days
    And the user goes to the appliance page of the Toploader
    Then they see a diagram with power consumption values of the Toploader
    And they see the power consumption of the Toploader
    And they see the running state of the Toploader
    Given they go to the appliance configuration page of the Toploader
    When they successfully submit the change of the name to Machine with a hole at the top
    Given they go to the appliance page of Machine with a hole at the top
    Then they see a diagram with the previous power consumption values
    And they see the power consumption of the Machine with a hole at the top
    And they see the running state of the Machine with a hole at the top

  Scenario: The user can indicate that an appliances, which is loadable can, needs unloading and unload it afterwards.
    Given the user goes to the virtual entities page
    When they click the needs unloading button of appliance Washer Kai
    Then they see the running state of the Washer Kai being loaded after a refresh
    When they click the unload button of appliance Washer Kai
    Then they see the running state of the Washer Kai being idling after a refresh


  Scenario: Chargeable appliances have state charging when they consume power.
    Given the user goes to the virtual entities page
    Then they see the power state of the Floor cleaner droelf thousand being idling after a refresh
    When the power consumption of the Floor cleaner droelf thousand is updated to 22
    Then they see the power state of the Floor cleaner droelf thousand being charging after a refresh
    When the power consumption of the Floor cleaner droelf thousand is updated to 0
    Then they see the power state of the Floor cleaner droelf thousand being idle after a refresh

  Scenario: Appliances which are not loadable don't have a button to indicate that it needs unloading.
    Given the user goes to the virtual entities page
    Then they don't see the needs unloading button of appliance Coffee machine

  Scenario: The coffee machine needs to be cleaned after each run.
    Given the user goes to the virtual entities page
    Then they see the power state of the Coffee machine being idling after a refresh
    When the power consumption of the Coffee machine is updated to 1201
    When the power consumption of the Coffee machine is updated to 42
    When the power consumption of the Coffee machine is updated to 50
    Then they see the running state of the Coffee machine being running after a refresh
    When the power consumption of the Coffee machine is updated to 0
    Then they see the power state of the Coffee machine being idle after a refresh
    Then they see the clean button of appliance Coffee machine
    When they click the clean button of appliance Coffee machine
    Then they see the notice dirt button of appliance Coffee machine
