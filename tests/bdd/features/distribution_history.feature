Feature: Distribution history

  Scenario: Host views distribution history
    Given I host a room
    Then I should see the distribution history empty state
    When a second user joins the room
    Then I should see the distribution history chart
