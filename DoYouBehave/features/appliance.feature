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
    Then the user sees a diagram with power consumption values
    Given they go to the appliance configuration page of the Toploader
    When they successfully submit the change of the name to Machine with a hole at the top
    Given they go to the appliance page of Machine with a hole at the top
    Then they see a diagram with the previous power consumption values