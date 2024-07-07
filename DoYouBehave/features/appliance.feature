Feature: The user can change the name of an appliance. The appliance is just renamed, all information is still there,
  i.e. the watt and its status. The appliance keeps its history of power consumption measurements, too.

  Scenario: The user can change the name of an appliance and is redirected to the new page where the name has changed.
    Given the user goes to the appliance configuration page of the Washing machine
    Then they see an input for the name having value Washing machine
    When they change the name to Machine making dirty clothes clean again
    And they submit the form
    Then they see a success message
    And they are on the appliance configuration page of Machine making dirty clothes clean again
    And the main headline contains Machine making dirty clothes clean again
