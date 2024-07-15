Feature: The user can see configurations of the room 'Hallway' and change its name.

  Scenario: The user sees the name and can change it.
    Given the user goes to the room configuration page of the Hallway
    Then they see an input for the name having value Hallway
