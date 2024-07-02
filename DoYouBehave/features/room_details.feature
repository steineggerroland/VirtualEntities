Feature: The user can see the static configuration of the Kitchen room and change its name.

  Scenario: The user navigates to the details page
    Given the user goes to the virtual entities page
    When they click on the Kitchen
    Then they are redirected to the room details page
    And the main headline contains Kitchen

  Scenario: The user sees the Kitchens room climate and updates.
    Given the user goes to the room details page of the Kitchen
    Then the user sees the temperature for the Kitchen
    And the user sees the humidity for the Kitchen
    When the room climate of the Kitchen is updated
    Then the user sees the new temperature for the Kitchen after a refresh
    And the user sees the new humidity for the Kitchen after a refresh

  Scenario: the user sees a diagram with the room climate, i.e., temperature and humidity.
    Given the user goes to the room details page of the Kitchen
    Then the user sees a diagram with temperature values
    And the user sees a diagram with humidity values
    When the room climate of the Kitchen is updated
    Then the user sees the diagram with updated temperature values
    And the user sees the diagram with updated humidity values

  Scenario: The user navigates to the configuration page of the room
    Given the user goes to the room details page of the Kitchen
    When they click the room configuration button
    Then they are redirected to the room configuration page
