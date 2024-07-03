Feature: Showing general information of virtual entities

  Scenario: All virtual entity types are present
    Given the user goes to the virtual entities page
    Then they see rooms in the room catalog
    And they see appliances in the appliance depot
    And they see person in the register of persons

  Scenario: The user sees all rooms
    Given the user goes to the virtual entities page
    Then they see the rooms Bathroom, Living room, Parents bedroom, Kitchen, Terrace

  Scenario: The user sees all appliances
    Given the user goes to the virtual entities page
    Then they see the appliances Dishwasher, Dryer

  Scenario: The user sees all persons
    Given the user goes to the virtual entities page
    Then they see the persons Robin, Ash

  Scenario: Power consumption updates are displayed
    Given the user goes to the virtual entities page
    When the power consumption of the Dryer is updated
    Then the user sees the new power consumption of the Dryer after a refresh

  Scenario: The different status of an appliance are displayed, i.e.,
  idle, running with duration and needing treatment.
    Given the user goes to the virtual entities page
    When the power consumption of the Dishwasher is updated to 0
    Then the user sees the new running state of the Dishwasher being idling after a refresh
    When the power consumption of the Dishwasher is updated to 1024
    Then the user sees the new running state of the Dishwasher being running after a refresh
    When the power consumption of the Dishwasher is updated to 5
    Then the user sees the new running state of the Dishwasher being loaded after a refresh

  Scenario: Room climate updates are displayed
    Given the user goes to the virtual entities page
    When the room climate of the Kitchen is updated
    Then the user sees the new temperature of the Kitchen after a refresh
    And the user sees the new humidity of the Kitchen after a refresh
