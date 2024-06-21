Feature: The user can see configurations of the room 'Hallway' and change its name.

  Scenario: The user sees the name and can change it.
    Given the user goes to the room configuration page of the Hallway
    Then they see an input for the name having value Hallway
    When they change the name to The room connecting several other rooms
    And they submit the form
    Then they see a success message
    And they are on to the room configuration page
    And the main headline contains The room connecting several other rooms
