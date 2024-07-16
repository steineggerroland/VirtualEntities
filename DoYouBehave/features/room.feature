Feature: The user can change the name of a room. The room keeps all its information, i.e. the temperature and
  humidity history and its status. It even works for rooms with a long measure history.

  Scenario: The user can change the name of a room and is redirected to the room page with the new name.
    Given the user goes to the room configuration page of the Lobby
    When they change the name to Foyer
    And they submit the form
    Then they see a success message
    And they are on the room configuration page of the Foyer
    And the main headline contains Foyer

  Scenario: There is a room with a longer history of measures. When renaming the room, the history is still there.
    Given 40000 room climate measures are created for the Storeroom spread over the last 14 days
    And they go to the room details page of the Storeroom
    Then they see a diagram with temperature values of the Storeroom
    And they see the temperature rating of the Storeroom
    And they see a diagram with humidity values of the Storeroom
    And they see the humidity rating of the Storeroom
    Given the user goes to the room configuration page of the Storeroom
    When they successfully submit the change of the name to Warehouse
    Given the user goes to the room details page of the Warehouse
    Then they see the diagram with the previous temperature values of the Warehouse
    And they see the previous temperature rating of the Warehouse
    And they see the diagram with the previous humidity values of the Warehouse
    And they see the previous humidity rating of the Warehouse
