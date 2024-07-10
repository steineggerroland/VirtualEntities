Feature: The user can see configurations of an appliance and change its name.

  Scenario: The user can basic information of the dryer.
    Given the user goes to the appliance configuration page of the Dryer
    Then the main headline contains Dryer
    And they see an input for the name having value Dryer
