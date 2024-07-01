Feature: The user can see the details of a person.

  Scenario: The user navigates to the persons' details page
    Given the user goes to the virtual entities page
    When they click on the name Robin
    Then they are redirected to the person details page
    And the main headline contains Robin

  Scenario: The user sees the private calendar of Robin and appointments.
    Given the user goes to the person details page of Robin
    Then they see the calendar called Robin Private
    When a new appointment for calendar Robin Private is created
    Then the user sees the new appointment after a refresh

  Scenario: The user navigates to the person configuration.
    Given the user goes to the person details page of Robin
    When they click the person configuration button
    Then they are redirected to the person configuration page
