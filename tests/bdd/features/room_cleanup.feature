Feature: Room cleanup

  Scenario: Disconnected user is removed from user status after timeout
    Given I host a room
    Then I should see info message "No status history yet"
    When a second user joins the room
    And the app cycled once
    Then there should be more than zero participants in my room
    Then one user should be in the room
    When the second user closes their session
    And the user removal timeout has passed
    And the app cycled once
    Then no more users should be in the room

  Scenario: Room host disconnects
    Given I host a room
    When a second user joins the room
    When I close my session
    And the user removal timeout has passed
    Then the second user should be on the room selection screen
