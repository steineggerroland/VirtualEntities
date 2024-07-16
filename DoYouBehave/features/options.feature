Feature: The user can set options for the page which are applied to every page they visit during a visit.


  Scenario: The user activates dark mode.
    Given they go to the home page
    When they activate dark mode
    Then the dark mode is active

  Scenario: The user activates fullscreen mode.
    Given they go to the home page
    When they activate fullscreen mode
    Then the fullscreen mode is active

  Scenario: The user activates refresh interval.
    Given they go to the home page
    When they activate refresh mode
    Then the refresh interval is set to 30

  Scenario: Options keep active. The user selects dark mode and the option is still active when going to other pages.
    Given they go to the home page
    When they activate dark mode
    When they click on the Dryer
    Then they are on the appliance page of Dryer
    And the dark mode is still active
