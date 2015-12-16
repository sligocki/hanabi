class Card:
  def __init__(self, color, num):
    self.color = color
    self.num = num  # Note: -1 from card game 1->0, 5->4
    # TODO: Maybe visibility?

class State:
  def __init__(self, num_players):
    self.num_players = num_players
    self.hand_size = 5
    self.num_colors = 5
    self.num_distrib = [5, 2, 2, 2, 1]

    self.deck = []
    for color in range(self.num_colors):
      for num, count in enumerate(self.num_distrib):
        self.deck += [Card(color, num)] * count
    random.shuffle(self.deck)

    self.remaining = [[5, 2, 2, 2, 1] for x in range(self.num_colors)]

    self.hands = [[self.draw() for _ in range(self.hand_size)]
                  for _ in range(num_players)]

  def draw(self):
    card = self.deck.pop()
    self.remaining[card.color][card.num] -= 1
    assert self.remaining[card.color][card.num] >= 0
    return card
