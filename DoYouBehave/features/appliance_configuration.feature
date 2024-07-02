Feature: The user can see configurations of an appliance and change its name.

  Scenario: The user sees the name and can change it.
    Given the user goes to the appliance configuration page of the Washing machine
    Then they see an input for the name having value Washing machine
    When they change the name to Machine making dirty clothes clean again
    And they submit the form
    Then they see a success message
    And they are on to the appliance configuration page
    And the main headline contains Machine making dirty clothes clean again
