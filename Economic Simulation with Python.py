import pygame
import random
import math
import logging
import time
import csv
import os

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize Pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Trade Simulation")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
STRATEGIES = ["Perfect Substitutes", "Perfect Complements", "Cobb-Douglas"]
STRATEGY_COLORS = {
    "Perfect Substitutes": (255, 0, 0),  # Red
    "Perfect Complements": (0, 255, 0),  # Green
    "Cobb-Douglas": (0, 0, 255),        # Blue
}

# Fonts
font = pygame.font.SysFont(None, 30)

# Game Constants
STRATEGIES = list(STRATEGY_COLORS.keys())
TRADE_RADIUS = 50
TRADE_AMOUNT = 5
NUM_PLAYERS = 10
MIN_PLAYERS = 7
rare_event_total = 0
FRAME_DELAY = 20  # milliseconds
headers = ['Player', 'Strategy', 'Time Period', 'Resource', 'Currency', 
           'Trade Count', 'Rare Event Occurred', 'Rare Event Type', 'Strategy Changed', 'Profit']

# Timer for seconds counter
start_time = time.time()

RARE_EVENT_PROB = {
    "crash": 0.1,  # P(Crash)
    "recession_given_crash": 0.5,  # P(Recession | Crash)
    "depression_given_recession": 0.20,  # P(Depression | Recession)
    "fallout_given_depression": 0.10  # P(Economic Fallout | Depression)
}

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 10
        self.scanning_radius = TRADE_RADIUS
        self.id = id
        self.resource = random.randint(20, 50)
        self.currency = random.randint(20, 50)
        self.strategy = random.choice(STRATEGIES)
        self.color = STRATEGY_COLORS[self.strategy]
        self.dx = random.choice([-1, 1]) * random.randint(1, 3)
        self.dy = random.choice([-1, 1]) * random.randint(1, 3)
        self.cooldown = 0
        self.is_trading = False
        self.trade_counter = 0  # Track trades
        self.rare_event_counter = 0  # Track how many rare events occurred
        self.rare_event_type = None  # Store the type of rare event

    def can_trade_with(self, other):
        """Check if trade conditions are met with another player."""
        # Add trade condition checks (for example, within trade radius)
        distance = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        return distance <= self.scanning_radius  # Example condition

    def move(self, other_players=None):
        """Update the player's position and handle interactions."""
        if other_players is None:
            other_players = []  # Default to an empty list

        # Interact with other players and bounce upon trade
        for other in other_players:
            if other != self:  # Avoid self-interaction
                distance = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
                if distance <= self.radius + other.radius:  # Collision or interaction
                    if self.can_trade_with(other):  # Check if trade conditions are met
                        # Move in the opposite direction after trade
                        angle = math.atan2(self.y - other.y, self.x - other.x)
                        self.dx = -self.dx + random.randint(-1, 1)  # Reverse and add randomness
                        self.dy = -self.dy + random.randint(-1, 1)  # Reverse and add randomness
                        other.dx = -other.dx + random.randint(-1, 1)  # Reverse and add randomness
                        other.dy = -other.dy + random.randint(-1, 1)  # Reverse and add randomness

                        # Limit movement adjustments to avoid excessive speed
                        self.dx = max(-3, min(3, self.dx))  # Limit to a range of -3 to 3
                        self.dy = max(-3, min(3, self.dy))  # Limit to a range of -3 to 3
                        other.dx = max(-3, min(3, other.dx))  # Limit to a range of -3 to 3
                        other.dy = max(-3, min(3, other.dy))  # Limit to a range of -3 to 3

                        # Cooldown to prevent immediate repeat interaction
                        self.cooldown = 10
                        other.cooldown = 10

        # Update position
        self.x += self.dx
        self.y += self.dy

        # Boundary checks to ensure players stay within screen bounds
        if self.x - self.radius < 0:  # Left edge
            self.x = self.radius  # Prevent going off-screen
            self.dx = -self.dx  # Reverse direction
        elif self.x + self.radius > WIDTH:  # Right edge
            self.x = WIDTH - self.radius  # Prevent going off-screen
            self.dx = -self.dx  # Reverse direction

        if self.y - self.radius < 0:  # Top edge
            self.y = self.radius  # Prevent going off-screen
            self.dy = -self.dy  # Reverse direction
        elif self.y + self.radius > HEIGHT:  # Bottom edge
            self.y = HEIGHT - self.radius  # Prevent going off-screen
            self.dy = -self.dy  # Reverse direction

        # Gradually decrease the movement speed if player is in the buffer zone
        buffer_zone = 30  # Distance from the screen edges where movement will change
        edge_sensitivity = 0.05  # Controls how sharply the player turns at the edges

        # Decrease cooldown timer
        if self.cooldown > 0:
            self.cooldown -= 1

    def evaluate_trade_ratio(self):
        """Determine the trade ratio based on the player's strategy."""
        if self.strategy == "Perfect Substitutes":
            # Linear trade-off: 1 unit of resource = 1 unit of currency
            return self.resource / self.currency if self.currency != 0 else float('inf')
        elif self.strategy == "Perfect Complements":
            # Complementary: utility based on the minimum of resource and currency
            return min(self.resource, self.currency)
        elif self.strategy == "Cobb-Douglas":
            # Cobb-Douglas utility function with weights for resources and currency
            alpha = 0.5  # Example: equal preference for resources and currency
            return (self.resource ** alpha) * (self.currency ** (1 - alpha))
        return 1  # Default for unknown strategies

    def trade(self, other):
        if self.cooldown == 0 and other.cooldown == 0:
            distance = math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
            if distance <= self.scanning_radius:
                # Evaluate trade-off based on strategies
                self_trade_ratio = self.evaluate_trade_ratio()
                other_trade_ratio = other.evaluate_trade_ratio()

                # Trade decision based on valuation alignment
                if self_trade_ratio > other_trade_ratio:
                    # Self values resources more; trade more resources for currency
                    resource_trade = min(TRADE_AMOUNT, self.resource)
                    currency_trade = min(TRADE_AMOUNT, other.currency)
                    self.resource -= resource_trade
                    self.currency += currency_trade
                    other.resource += resource_trade
                    other.currency -= currency_trade
                elif self_trade_ratio < other_trade_ratio:
                    # Self values currency more; trade more currency for resources
                    resource_trade = min(TRADE_AMOUNT, other.resource)
                    currency_trade = min(TRADE_AMOUNT, self.currency)
                    self.resource += resource_trade
                    self.currency -= currency_trade
                    other.resource -= resource_trade
                    other.currency += currency_trade
                else:
                    # Equal valuation; trade equal amounts
                    resource_trade = min(TRADE_AMOUNT, self.resource, other.resource)
                    currency_trade = min(TRADE_AMOUNT, self.currency, other.currency)
                    self.resource -= resource_trade
                    self.currency -= currency_trade
                    other.resource += resource_trade
                    other.currency += currency_trade

                # Increment trade counters
                self.trade_counter += 1  # Increment trade count for the player
                other.trade_counter += 1  # Increment trade count for the other player

                # Set cooldowns and increment trade counters
                self.cooldown = 50
                other.cooldown = 50
                return True
        return False
    
    def adjust_strategy(self):
        """Adjust strategies based on recent trade success."""
        previous_strategy = self.strategy  # Store the previous strategy before any changes

        if self.trade_counter % 10 == 0:  # Adjust strategy at regular intervals (every 10 trades)
            if self.resource > self.currency:
                self.strategy = "Perfect Substitutes"
            elif self.resource < self.currency:
                self.strategy = "Cobb-Douglas"
            else:
                self.strategy = "Perfect Complements"

            # If the strategy has changed, record the change
            if self.strategy != previous_strategy:
                self.record_strategy_change(previous_strategy)  # Only log the change if it's different

            # Reassign color based on the new strategy
            self.color = STRATEGY_COLORS.get(self.strategy, "default_color")  # Update the color based on new strategy

            # Update previous_strategy to current strategy
            self.previous_strategy = self.strategy

    def record_strategy_change(self, previous_strategy):
        """Record the player's strategy change to a CSV file."""
        current_time = time.time() - start_time  # Time elapsed since the start of the game
        rare_event_occurred = rare_event_total > 0  # Whether a rare event has occurred
        strategy_changed = 1 if self.strategy != previous_strategy else 0  # 1 if strategy changed, 0 if not

        # Write to CSV file
        with open('game_data.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.player_id, self.strategy, current_time, self.resource,
                            self.currency, self.trade_counter, rare_event_occurred, self.rare_event_type, strategy_changed])

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.radius)
        label = f"R:{self.resource} C:{self.currency} S:{self.strategy[:2]}"
        text = font.render(label, True, BLACK)
        screen.blit(text, (self.x - self.radius, self.y - self.radius - 20))

        trade_count_label = font.render(f"Trades: {self.trade_counter}", True, BLACK)
        screen.blit(trade_count_label, (self.x - self.radius, self.y + self.radius))

    def invest_resources(self, firm):
        """Invest a portion of resources in the firm."""
        invest_amount = self.resource * 0.1  # 10% of resources, as an example
        if invest_amount <= self.resource:
            self.resource -= invest_amount
            firm.accept_investment(self.id, invest_amount)  # Pass amount directly to the firm

    def receive_returns(self, amount):
        """Receive returns from the firm."""
        self.currency += amount

class Firm:
    def __init__(self, interest_rate=0.05):
        self.interest_rate = interest_rate
        self.currency_reserves = 0
        self.investments = {}  # Tracks investments per player

    def accept_investment(self, player_id, amount):
        """Accepts an investment from a player."""
        if player_id not in self.investments:
            self.investments[player_id] = 0
        self.investments[player_id] += amount
        self.currency_reserves += amount

    def process_returns(self):
        """Calculates and returns investment returns to players."""
        returns = {}
        for player_id, invested_amount in self.investments.items():
            profit = int(round(invested_amount * self.interest_rate))  # Calculate profit only
            returns[player_id] = profit  # Only return the profit
            self.currency_reserves -= profit  # Deduct the profit from firm’s reserves

        self.investments.clear()
        return returns

# Simulation step for resource investment and returns
def simulation_step(players, firm):
    # Players invest a portion of their resources
    for player in players:
        player.invest_resources(firm)  # Let the player decide how much to invest

    # Firm processes and distributes returns
    returns = firm.process_returns()
    for player_id, return_amount in returns.items():
        for player in players:
            if player.id == player_id:
                player.receive_returns(return_amount)

    # After returns are processed, save the updated data (including profits/returns)
    elapsed_time = int((time.time() - start_time) / 5)  # Elapsed time in 5-second intervals
    save_to_csv(players, elapsed_time)  # Save to CSV after each return distribution

def redistribute_resources(players):
    total_resources = sum(player.resource for player in players)
    total_currency = sum(player.currency for player in players)

    for player in players:
        other_players_resource = total_resources - player.resource
        other_players_currency = total_currency - player.currency
        
        # Check if the player has more resources and currency combined than all others
        if player.resource + player.currency > other_players_resource + other_players_currency:
            # Slash the player's resources and currency to fit within average limits
            player.resource = int(player.resource * 0.75)
            player.currency = int(player.currency * 0.75)

def rare_event(players, elapsed_time):
    """
    Simulate rare events using an event chain for Stock Market Crash, Recession, Depression, and Economic Fallout.
    Apply reductions to resources and currency based on event type to all players.
    Ensure the event affects only one time period.
    """
    global rare_event_total  # Reference the global rare_event_total variable
    event_occurred = False  # Flag to track if any rare event occurred

    # Initialize event chain
    event_chain = [
        ("Stock Market Crash", RARE_EVENT_PROB["crash"], 0.15),
        ("Recession", RARE_EVENT_PROB["recession_given_crash"], 0.10),
        ("Depression", RARE_EVENT_PROB["depression_given_recession"], 0.05),
        ("Economic Fallout", RARE_EVENT_PROB["fallout_given_depression"], 0.20)
    ]

    current_event = None
    cumulative_reduction = 0  # Accumulated reduction from all events

    # Evaluate rare event probability for the current time period
    if random.random() <= RARE_EVENT_PROB["crash"]:
        for event_name, prob, reduction in event_chain:
            if random.random() <= prob:
                current_event = event_name
                cumulative_reduction += reduction
                logging.info(f"{current_event} occurred! Total reduction: {cumulative_reduction * 100:.0f}%.")
                event_occurred = True
            else:
                break  # Stop the chain if a condition fails

        # Apply the cumulative reduction to all players if any event occurred
        if event_occurred:
            for player in players:
                player.resource = max(0, int(player.resource * (1 - cumulative_reduction)))
                player.currency = max(0, int(player.currency * (1 - cumulative_reduction)))

                # Update player's rare event state to the last event in the chain
                player.rare_event_type = current_event
                player.rare_event_counter += 1

            # Increment the global rare event counter
            rare_event_total += 1

            # Log the rare event update
            logging.info(f"Rare event chain completed. Final event: {current_event}. Total rare events: {rare_event_total}.")
        else:
            # Clear rare event types for all players to ensure no lingering effects
            for player in players:
                player.rare_event_type = None

def clear_csv_on_exit(filename="game_data.csv"):
    # Remove the CSV file to ensure it's overwritten when the program starts again
    if os.path.exists(filename):
        os.remove(filename)

def save_to_csv(players, elapsed_time, filename="game_data.csv"):
    headers = ['Player', 'Strategy', 'Time Period', 'Resource', 'Currency', 
               'Trade Count', 'Rare Event Occurred', 'Rare Event Type', 'Strategy Changed', 'Profit']  # Correct header with 'Strategy Changed'

    # Open the file in append mode ('a') to add data during each time period
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)

        # Prepare headers only if the file is empty (initial run)
        if os.stat(filename).st_size == 0:
            writer.writerow(headers)

        # Keep track of the unique entries for this time period
        logged_players = set()  # Set to store players already logged for this time period

        # Prepare data rows and write them to the CSV file
        for i, player in enumerate(players):  # Use index `i` as unique player ID
            if player.x not in logged_players:  # Use player position as a unique identifier
                logged_players.add(player.x)  # Mark this player as logged for this time period
                rare_event_occurred = 1 if player.rare_event_type else 0
                rare_event_type = player.rare_event_type if player.rare_event_type else "None"
                
                # Add profit data (return from the firm)
                profit = player.currency - (player.resource + player.trade_counter * TRADE_AMOUNT)  # Simplified calculation for profit
                
                # Construct row
                row = [f"Player_{i}", player.strategy, elapsed_time, player.resource, 
                       player.currency, player.trade_counter, rare_event_occurred, rare_event_type,
                       1 if player.strategy != player.previous_strategy else 0, profit]  # Strategy Changed column
                writer.writerow(row)

# Game Loop
def game_loop():
    start_time = time.time()
    players = [Player(random.randint(100, WIDTH - 100), random.randint(100, HEIGHT - 100)) for _ in range(NUM_PLAYERS)]
    firm = Firm()  # Create the firm instance
    running = True
    total_trades = 0  # Initialize total_trades here before any use
    last_logged_time = 0  # Variable to track the last logged time period
    last_profit_time = 0  # Track the last time the profit was calculated

    while running:
        screen.fill(WHITE)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Time counter (in terms of 5-second intervals)
        elapsed_time = int((time.time() - start_time) / 5)

        # Only save to CSV at the end of each time period, to avoid duplicates
        if elapsed_time > last_logged_time:
            save_to_csv(players, elapsed_time)  # Save data at the end of the period
            last_logged_time = elapsed_time  # Update the last logged time

        # Update the simulation (Investments, Returns, etc.) once per time period
        if elapsed_time > last_profit_time:
            simulation_step(players, firm)  # Handle investments and returns for the firm
            returns = firm.process_returns()  # Process the returns and give them to the players
            for player_id, return_amount in returns.items():
                for player in players:
                    if player.id == player_id:
                        player.receive_returns(return_amount)

            last_profit_time = elapsed_time  # Update the last time the profit was calculated

        # Render the time counter
        time_counter_label = font.render(f"Time: {elapsed_time}", True, BLACK)
        screen.blit(time_counter_label, (WIDTH - 150, 10))

        # Update and draw players
        for player in players[:]:
            player.move(players)  # Pass the other players list
            player.draw(screen)

            # Interaction with other players
            for other in players:
                if player != other:
                    if player.trade(other):
                        total_trades += 1  # Increment trade count when a trade occurs

            # Remove players with no resources and currency
            if player.resource == 0 and player.currency == 0:
                players.remove(player)

        if elapsed_time > last_logged_time or random.random() < RARE_EVENT_PROB["crash"]:
            rare_event(players, elapsed_time)

        # Add new players if there are fewer than the minimum
        if len(players) < MIN_PLAYERS:
            new_player = Player(random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50))
            players.append(new_player)

        # Inside the game loop, call the function after updating players
        redistribute_resources(players)

        # Trade and rare event counters
        trade_total = sum(player.trade_counter for player in players)
        rare_event_count = rare_event_total  # Reflect the global rare event count

        # Render and display the labels
        trade_label = font.render(f"Trades: {trade_total}", True, BLACK)
        rare_event_label = font.render(f"Rare Events: {rare_event_count}", True, BLACK)

        screen.blit(trade_label, (10, 10))
        screen.blit(rare_event_label, (10, 40))

        # Update the display
        pygame.display.flip()
        pygame.time.delay(FRAME_DELAY)

    pygame.quit()

# Overwrite CSV file at program start (if it doesn't exist)
if __name__ == "__main__":
    filename = 'game_data.csv'
    
    # Clear the CSV file at program exit (overwrite for the next run)
    clear_csv_on_exit(filename)

    # Check if the CSV file exists, if not, write the header
    if not os.path.exists(filename):
        with open(filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Updated header to include strategy changes
            writer.writerow(['Player', 'Strategy', 'Time Period', 'Resource', 'Currency', 
                             'Trade Count', 'Rare Event Occurred', 'Rare Event Type', 'Strategy Changed', 'Profit'])

    # Start the game loop (this will handle appending data during each time period)
    game_loop()