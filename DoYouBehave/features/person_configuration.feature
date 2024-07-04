Feature: The user can see configurations of a person and change its name.

  Scenario: The user sees the name and can change it.
    Given the user goes to the person configuration page of Billy
    Then they see an input for the name having value Billy
    When they change the name to Bill without y
    And they submit the form
    Then they see a success message
    And they are on the person configuration page
    And the main headline contains Bill without y
