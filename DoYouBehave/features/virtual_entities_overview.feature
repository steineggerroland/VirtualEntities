Feature: Showing general information of virtual entities

  Scenario: All virtual entity types are present
    Given the user goes to the virtual entities page
    Then they see rooms in the room catalog
    And they see appliances in the appliance deoot
    And they see person in the register of persons

  Scenario: The user sees all rooms
    Given the user goes to the virtual entities page
    Then they see the rooms Bathroom, Living room, Parents bedroom, Kitchen, Terrace

  Scenario: The user sees all appliances
    Given the user goes to the virtual entities page
    Then they see the appliances Dishwasher, Washing machine, Dryer

  Scenario: The user sees all persons
    Given the user goes to the virtual entities page
    Then they see the persons Robin, Ash
