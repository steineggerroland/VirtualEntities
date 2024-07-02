Feature: The user can see details of the Dryer appliance.

  Scenario: The user navigates to the details page
    Given the user goes to the virtual entities page
    When they click on the Dryer
    Then they are redirected to the appliance page
    And the main headline contains Dryer

  Scenario: The user sees clearly the type of appliance
    Given the user goes to the appliance page of the Dryer
    Then they see an icon indicating dryer being the type of appliance
    And they see the type is dryer

  Scenario: The user sees the power consumption and it updates on new messages
    Given the user goes to the appliance page of the Dryer
    When the power consumption of the Dryer is updated
    Then the user sees the new power consumption for the Dryer after a refresh

  Scenario: The user navigates to the configuration page of the appliance
    Given the user goes to the appliance page of the Dryer
    When they click the appliance configuration button
    Then they are redirected to the appliance configuration page
