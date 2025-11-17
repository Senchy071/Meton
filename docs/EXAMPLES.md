# Usage Examples

Real-world examples demonstrating Meton's capabilities.

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Code Understanding](#code-understanding)
3. [Code Review](#code-review)
4. [Test Generation](#test-generation)
5. [Refactoring](#refactoring)
6. [Documentation](#documentation)
7. [Debugging](#debugging)
8. [Project Workflows](#project-workflows)
9. [Advanced Use Cases](#advanced-use-cases)

---

## Getting Started

### Example 1: First Steps

```bash
# Start Meton
python meton.py

# Check status
> /status

╭─── Current Status ───────────────────────────────╮
│ Model:        qwen2.5-coder:32b                  │
│ Session:      3c8a9f2d-4b1e...                   │
│ Messages:     0                                  │
│ Tools:        5 enabled                          │
│ RAG:          ❌ not indexed                      │
╰──────────────────────────────────────────────────╯

# List available commands
> /help

# List tools
> /tools

Available Tools:
✅ file_operations - Read, write, list files
✅ code_executor - Execute Python code
❌ web_search - Web search (disabled)
✅ codebase_search - Semantic code search
✅ git_operations - Git integration
```

### Example 2: Simple Query

```bash
> What is the difference between a list and a tuple in Python?

💬 Lists and tuples are both sequence types in Python, but have key differences:

**Lists:**
- Mutable (can be modified after creation)
- Defined with square brackets: [1, 2, 3]
- Methods: append(), remove(), sort(), etc.
- Use when you need to modify the collection

**Tuples:**
- Immutable (cannot be modified after creation)
- Defined with parentheses: (1, 2, 3)
- Fewer methods (no append, remove, etc.)
- Faster than lists
- Use for fixed collections or as dictionary keys

**Example:**
```python
# List (mutable)
my_list = [1, 2, 3]
my_list.append(4)  # OK

# Tuple (immutable)
my_tuple = (1, 2, 3)
my_tuple.append(4)  # ERROR
```
```

---

## Code Understanding

### Example 3: Index and Search Codebase

```bash
# Index a FastAPI project
> /index /media/development/projects/fastapi-demo

🔍 Indexing /media/development/projects/fastapi-demo...
Found 87 Python files

Processing files... ━━━━━━━━━━ 100% 87/87 00:12

✅ Complete! Indexed 87 files, 423 chunks in 12.3s
RAG enabled ✅
Codebase search enabled ✅

# Search for authentication code
> How does authentication work in this project?

💭 THOUGHT: Using codebase_search to find authentication logic
🔧 ACTION: codebase_search
📥 INPUT: {"query": "authentication login user verify JWT token"}

📊 OBSERVATION: Found 5 relevant files:
1. api/auth.py:45-89 (score: 0.92)
2. core/security.py:12-34 (score: 0.87)
3. models/user.py:23-45 (score: 0.78)
...

💬 Based on the codebase:

**Authentication Flow:**
1. **Login** (api/auth.py:45-67)
   - User submits username/password
   - Credentials validated against database
   - JWT token generated if valid

2. **Token Generation** (core/security.py:12-34)
   - Uses HS256 algorithm
   - Includes user_id and expiration
   - Expires after 24 hours

3. **Token Verification** (api/dependencies.py:18-29)
   - Middleware extracts token from Authorization header
   - Validates signature and expiration
   - Loads user from database

**Security Features:**
- Passwords hashed with bcrypt (cost factor 12)
- Tokens expire after 24 hours
- Refresh tokens supported
- CORS configured for specific origins
```

### Example 4: Explain Complex Code

```bash
> Explain this code in detail:

def fibonacci_memoized(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memoized(n-1, memo) + fibonacci_memoized(n-2, memo)
    return memo[n]

💬 **Code Explanation:**

**Purpose:**
Calculate Fibonacci numbers using memoization for efficiency.

**How it Works:**
1. **Memoization Check**: First checks if result for 'n' already calculated
2. **Base Case**: Returns n directly if n <= 1 (Fib(0)=0, Fib(1)=1)
3. **Recursive Calculation**: Calculates Fib(n-1) + Fib(n-2) if not memoized
4. **Cache Result**: Stores result in memo dictionary for future use

**Complexity Analysis:**
- Time: O(n) - Each number calculated once
- Space: O(n) - Memo dictionary stores n results

**Advantages:**
✅ Much faster than naive recursion (O(2^n))
✅ Simple to understand
✅ Automatic caching

**Issues:**
⚠️ **CRITICAL BUG**: Mutable default argument!
The memo={} is shared across all function calls, which can cause
unexpected behavior.

**Better Implementation:**
```python
def fibonacci_memoized(n, memo=None):
    if memo is None:
        memo = {}
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = fibonacci_memoized(n-1, memo) + fibonacci_memoized(n-2, memo)
    return memo[n]
```

Or use functools.lru_cache:
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
```
```

---

## Code Review

### Example 5: Security Review

```bash
> Review this code for security issues:

from flask import Flask, request, render_template_string
import sqlite3

app = Flask(__name__)

@app.route('/user/<user_id>')
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    conn = sqlite3.connect('database.db')
    result = conn.execute(query).fetchone()
    return render_template_string("<h1>User: {{name}}</h1>", name=result[1])

@app.route('/search')
def search():
    term = request.args.get('q')
    return render_template_string(f"<p>Searching for: {term}</p>")

💬 **Security Review Results:**

🚨 **CRITICAL Issues (Fix Immediately):**

**1. SQL Injection (Line 8)**
```python
query = f"SELECT * FROM users WHERE id = {user_id}"
```
**Risk:** Attacker can execute arbitrary SQL
**Example Attack:** `/user/1 OR 1=1; DROP TABLE users--`
**Fix:**
```python
query = "SELECT * FROM users WHERE id = ?"
result = conn.execute(query, (user_id,)).fetchone()
```

**2. Server-Side Template Injection (SSTI) (Line 16)**
```python
return render_template_string(f"<p>Searching for: {term}</p>")
```
**Risk:** Attacker can execute Python code on server
**Example Attack:** `?q={{config.items()}}`
**Fix:**
```python
return render_template_string("<p>Searching for: {{term}}</p>", term=term)
```

**3. Missing Input Validation (Lines 8, 15)**
- No validation of user_id (should be integer)
- No validation of search term
**Fix:**
```python
try:
    user_id = int(user_id)
except ValueError:
    return "Invalid user ID", 400
```

⚠️ **WARNING Issues:**

**4. No Error Handling (Line 9)**
- Database connection can fail
- Query can return None
**Fix:**
```python
try:
    conn = sqlite3.connect('database.db')
    result = conn.execute(query, (user_id,)).fetchone()
    if not result:
        return "User not found", 404
except sqlite3.Error as e:
    return "Database error", 500
finally:
    conn.close()
```

**5. Missing CSRF Protection**
- Flask app needs CSRF protection
**Fix:**
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

💡 **Recommendations:**

1. **Use ORM**: Consider SQLAlchemy instead of raw SQL
2. **Use Templates**: Store templates in files, not strings
3. **Add Logging**: Log security events
4. **Use HTTPS**: Ensure SSL/TLS in production
5. **Add Rate Limiting**: Prevent brute force attacks

**Corrected Code:**
```python
from flask import Flask, request, render_template, abort
from flask_wtf.csrf import CSRFProtect
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
csrf = CSRFProtect(app)

@app.route('/user/<int:user_id>')
def get_user(user_id):
    try:
        conn = sqlite3.connect('database.db')
        query = "SELECT * FROM users WHERE id = ?"
        result = conn.execute(query, (user_id,)).fetchone()

        if not result:
            abort(404)

        return render_template('user.html', name=result[1])
    except sqlite3.Error:
        abort(500)
    finally:
        if conn:
            conn.close()

@app.route('/search')
def search():
    term = request.args.get('q', '')
    # Sanitize input
    term = term[:100]  # Limit length
    return render_template('search.html', term=term)
```
```

---

## Test Generation

### Example 6: Generate Pytest Tests

```bash
> Generate pytest tests for this function:

def calculate_discount(price, discount_percent, min_purchase=0):
    """Calculate discounted price.

    Args:
        price: Original price
        discount_percent: Discount percentage (0-100)
        min_purchase: Minimum purchase for discount

    Returns:
        Discounted price
    """
    if price < min_purchase:
        return price
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return price * (1 - discount_percent / 100)

💬 **Generated Test Suite:**

```python
import pytest

def test_calculate_discount_normal():
    """Test normal discount calculation."""
    result = calculate_discount(100, 20)
    assert result == 80.0, "20% off $100 should be $80"

def test_calculate_discount_no_discount():
    """Test with 0% discount."""
    result = calculate_discount(100, 0)
    assert result == 100.0, "0% discount should return original price"

def test_calculate_discount_full_discount():
    """Test with 100% discount."""
    result = calculate_discount(100, 100)
    assert result == 0.0, "100% discount should be free"

def test_calculate_discount_below_minimum():
    """Test purchase below minimum threshold."""
    result = calculate_discount(50, 20, min_purchase=100)
    assert result == 50.0, "No discount if below minimum"

def test_calculate_discount_at_minimum():
    """Test purchase at exact minimum threshold."""
    result = calculate_discount(100, 20, min_purchase=100)
    assert result == 80.0, "Discount applies at minimum threshold"

def test_calculate_discount_above_minimum():
    """Test purchase above minimum threshold."""
    result = calculate_discount(150, 20, min_purchase=100)
    assert result == 120.0, "Discount applies above minimum"

def test_calculate_discount_invalid_negative():
    """Test invalid negative discount."""
    with pytest.raises(ValueError, match="between 0 and 100"):
        calculate_discount(100, -10)

def test_calculate_discount_invalid_over_100():
    """Test invalid discount over 100%."""
    with pytest.raises(ValueError, match="between 0 and 100"):
        calculate_discount(100, 150)

def test_calculate_discount_edge_case_zero_price():
    """Test edge case with zero price."""
    result = calculate_discount(0, 20)
    assert result == 0.0, "Discount on $0 should be $0"

def test_calculate_discount_decimal_discount():
    """Test with decimal discount percentage."""
    result = calculate_discount(100, 15.5)
    assert result == 84.5, "15.5% off $100 should be $84.50"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

**Coverage: 100%**
- Normal cases: ✅
- Edge cases: ✅
- Error cases: ✅
- Boundary conditions: ✅

**To run:**
```bash
pytest test_calculate_discount.py -v
```
```

---

## Refactoring

### Example 7: Refactor Complex Code

```bash
> Suggest refactorings for this code:

def process_order(order_data):
    if order_data['status'] == 'pending':
        if order_data['payment_method'] == 'credit_card':
            if order_data['amount'] > 0:
                if validate_card(order_data['card_number']):
                    charge_card(order_data['card_number'], order_data['amount'])
                    send_confirmation_email(order_data['email'])
                    update_inventory(order_data['items'])
                    mark_order_complete(order_data['order_id'])
                    return True
                else:
                    return False
            else:
                return False
        elif order_data['payment_method'] == 'paypal':
            if order_data['amount'] > 0:
                if process_paypal(order_data['paypal_email'], order_data['amount']):
                    send_confirmation_email(order_data['email'])
                    update_inventory(order_data['items'])
                    mark_order_complete(order_data['order_id'])
                    return True
                else:
                    return False
            else:
                return False
    return False

💬 **Refactoring Suggestions:**

**Issues Detected:**
1. 🔴 **Deep Nesting** (6 levels) - Hard to read
2. 🔴 **Code Duplication** - Repeated confirmation/inventory logic
3. 🔴 **Magic Strings** - 'pending', 'credit_card', etc.
4. 🔴 **Long Method** - Does too many things
5. 🔴 **Poor Error Handling** - Just returns False

**Refactored Code:**

```python
from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass

class OrderStatus(Enum):
    PENDING = "pending"
    COMPLETE = "complete"
    FAILED = "failed"

class PaymentMethod(Enum):
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"

@dataclass
class OrderData:
    order_id: str
    status: str
    payment_method: str
    amount: float
    email: str
    items: list
    card_number: str = None
    paypal_email: str = None

class OrderProcessor:
    """Handle order processing with different payment methods."""

    def process_order(self, order: OrderData) -> bool:
        """Process an order.

        Args:
            order: Order data

        Returns:
            True if successful, False otherwise
        """
        # Validation
        if not self._validate_order(order):
            return False

        # Process payment
        payment_successful = self._process_payment(order)
        if not payment_successful:
            return False

        # Complete order
        self._complete_order(order)
        return True

    def _validate_order(self, order: OrderData) -> bool:
        """Validate order data."""
        if order.status != OrderStatus.PENDING.value:
            return False
        if order.amount <= 0:
            return False
        return True

    def _process_payment(self, order: OrderData) -> bool:
        """Process payment based on method."""
        if order.payment_method == PaymentMethod.CREDIT_CARD.value:
            return self._process_credit_card(order.card_number, order.amount)
        elif order.payment_method == PaymentMethod.PAYPAL.value:
            return self._process_paypal(order.paypal_email, order.amount)
        else:
            raise ValueError(f"Unknown payment method: {order.payment_method}")

    def _process_credit_card(self, card_number: str, amount: float) -> bool:
        """Process credit card payment."""
        if not validate_card(card_number):
            return False
        return charge_card(card_number, amount)

    def _process_paypal(self, paypal_email: str, amount: float) -> bool:
        """Process PayPal payment."""
        return process_paypal(paypal_email, amount)

    def _complete_order(self, order: OrderData) -> None:
        """Complete order processing."""
        send_confirmation_email(order.email)
        update_inventory(order.items)
        mark_order_complete(order.order_id)

# Usage
processor = OrderProcessor()
order = OrderData(
    order_id="12345",
    status="pending",
    payment_method="credit_card",
    amount=99.99,
    email="user@example.com",
    items=[{"id": 1, "quantity": 2}],
    card_number="1234-5678-9012-3456"
)
success = processor.process_order(order)
```

**Improvements:**
✅ **Reduced Nesting** - From 6 to 2 levels
✅ **DRY Principle** - No code duplication
✅ **Type Safety** - Using Enums and dataclasses
✅ **Single Responsibility** - Each method does one thing
✅ **Better Naming** - Clear, descriptive names
✅ **Testability** - Easy to unit test each method
✅ **Extensibility** - Easy to add new payment methods

**Complexity Reduction:**
- Original: Cyclomatic Complexity = 12
- Refactored: Cyclomatic Complexity = 4 (per method)
```

---

## Documentation

### Example 8: Generate Docstrings

```bash
> Generate Google-style docstrings for this code:

class UserManager:
    def __init__(self, db_connection):
        self.db = db_connection

    def create_user(self, username, email, password, role='user'):
        hashed_pw = hash_password(password)
        user_id = self.db.insert_user(username, email, hashed_pw, role)
        return user_id

    def authenticate(self, username, password):
        user = self.db.get_user_by_username(username)
        if user and verify_password(password, user['password']):
            return user
        return None

💬 **Generated Documentation:**

```python
class UserManager:
    """Manage user accounts and authentication.

    This class provides methods for creating users and authenticating
    them against the database. Passwords are hashed using bcrypt.

    Attributes:
        db: Database connection instance for user operations.

    Example:
        >>> db = DatabaseConnection()
        >>> manager = UserManager(db)
        >>> user_id = manager.create_user("john", "john@example.com", "secret123")
        >>> user = manager.authenticate("john", "secret123")
    """

    def __init__(self, db_connection):
        """Initialize UserManager with database connection.

        Args:
            db_connection: Active database connection instance.
        """
        self.db = db_connection

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str = 'user'
    ) -> int:
        """Create a new user account.

        Hashes the provided password and stores the user in the database
        with the specified role.

        Args:
            username: Unique username for the account.
            email: User's email address.
            password: Plain-text password (will be hashed).
            role: User role. Defaults to 'user'. Options: 'user', 'admin'.

        Returns:
            Newly created user's ID.

        Raises:
            ValueError: If username already exists.
            ValueError: If email format is invalid.
            DatabaseError: If database insertion fails.

        Example:
            >>> manager.create_user("alice", "alice@example.com", "pass123")
            42
        """
        hashed_pw = hash_password(password)
        user_id = self.db.insert_user(username, email, hashed_pw, role)
        return user_id

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password.

        Retrieves user from database and verifies the provided password
        against the stored hash.

        Args:
            username: Username to authenticate.
            password: Plain-text password to verify.

        Returns:
            User dictionary with keys 'id', 'username', 'email', 'role'
            if authentication successful, None otherwise.

        Example:
            >>> user = manager.authenticate("alice", "pass123")
            >>> if user:
            ...     print(f"Welcome {user['username']}")
            Welcome alice
        """
        user = self.db.get_user_by_username(username)
        if user and verify_password(password, user['password']):
            return user
        return None
```
```

---

## Debugging

### Example 9: Debug Error

```bash
> Debug this error:

Traceback (most recent call last):
  File "app.py", line 67, in process_data
    result = data['items'][index]['price'] * quantity
KeyError: 'price'

Code context:
def process_data(data):
    total = 0
    for index, item in enumerate(data['items']):
        quantity = data['quantities'][index]
        result = item['price'] * quantity
        total += result
    return total

💬 **Debug Analysis:**

**Error:** KeyError: 'price'

**Root Cause:**
One or more items in `data['items']` don't have a 'price' key.

**Possible Reasons:**
1. Data structure inconsistency
2. Missing field in source data
3. Wrong key name (e.g., 'cost' instead of 'price')
4. Null/None item in list

**Additional Issues Found:**
1. **IndexError Risk**: If `data['quantities']` shorter than `data['items']`
2. **No Input Validation**: Doesn't check if keys exist
3. **No Type Checking**: Assumes price is numeric

**Debugging Steps:**

**Step 1: Add Logging**
```python
import logging

def process_data(data):
    logging.debug(f"Processing data: {data}")
    total = 0
    for index, item in enumerate(data['items']):
        logging.debug(f"Item {index}: {item}")  # See which item fails
        quantity = data['quantities'][index]
        result = item['price'] * quantity
        total += result
    return total
```

**Step 2: Add Validation**
```python
def process_data(data):
    # Validate input
    if 'items' not in data:
        raise ValueError("Missing 'items' key in data")
    if 'quantities' not in data:
        raise ValueError("Missing 'quantities' key in data")
    if len(data['items']) != len(data['quantities']):
        raise ValueError("Items and quantities length mismatch")

    total = 0
    for index, item in enumerate(data['items']):
        # Validate item
        if not item:
            raise ValueError(f"Item at index {index} is None/empty")
        if 'price' not in item:
            raise ValueError(f"Item at index {index} missing 'price' key. Keys: {item.keys()}")

        quantity = data['quantities'][index]
        result = item['price'] * quantity
        total += result
    return total
```

**Fixed Version with Better Error Handling:**
```python
from typing import List, Dict, Any

def process_data(data: Dict[str, Any]) -> float:
    """Calculate total price for items and quantities.

    Args:
        data: Dictionary with 'items' (list of dicts) and 'quantities' (list of ints)

    Returns:
        Total price

    Raises:
        ValueError: If data is invalid
    """
    # Validate structure
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    items = data.get('items', [])
    quantities = data.get('quantities', [])

    if not items:
        return 0.0

    if len(items) != len(quantities):
        raise ValueError(
            f"Items ({len(items)}) and quantities ({len(quantities)}) "
            f"must have same length"
        )

    total = 0.0
    for index, (item, quantity) in enumerate(zip(items, quantities)):
        # Validate item
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {index} is not a dictionary: {type(item)}")

        # Get price with default
        price = item.get('price')
        if price is None:
            raise ValueError(
                f"Item at index {index} missing 'price'. "
                f"Available keys: {list(item.keys())}"
            )

        # Validate types
        try:
            price = float(price)
            quantity = int(quantity)
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid price/quantity at index {index}: "
                f"price={price}, quantity={quantity}"
            ) from e

        total += price * quantity

    return total

# Usage with error handling
try:
    result = process_data(data)
    print(f"Total: ${result:.2f}")
except ValueError as e:
    print(f"Error processing data: {e}")
    # Log error, return default, or re-raise
```

**Test Cases:**
```python
import pytest

def test_process_data_valid():
    data = {
        'items': [{'price': 10.0}, {'price': 20.0}],
        'quantities': [2, 3]
    }
    assert process_data(data) == 80.0

def test_process_data_missing_price():
    data = {
        'items': [{'name': 'Item 1'}],
        'quantities': [1]
    }
    with pytest.raises(ValueError, match="missing 'price'"):
        process_data(data)

def test_process_data_length_mismatch():
    data = {
        'items': [{'price': 10.0}],
        'quantities': [1, 2]
    }
    with pytest.raises(ValueError, match="same length"):
        process_data(data)
```
```

---

## Project Workflows

### Example 10: Complete Project Workflow

```bash
# 1. Start new project
> /template create fastapi-api my-api-project

📁 Creating project from fastapi-api template...
✅ Created project structure
✅ Generated files: app.py, models.py, routes.py, ...
✅ Created virtual environment
✅ Installed dependencies

# 2. Index the project
> /index my-api-project

🔍 Indexing my-api-project...
✅ Indexed 15 files, 87 chunks

# 3. Understand project structure
> Explain the project structure and main components

💬 This FastAPI project follows a modular structure:

**Main Components:**
- `app.py`: Application entry point, CORS, middleware
- `routes/`: API endpoint definitions
- `models/`: Pydantic models for validation
- `database.py`: SQLAlchemy database connection
- `config.py`: Configuration management

**Architecture:**
- RESTful API with OpenAPI docs
- PostgreSQL database with SQLAlchemy ORM
- JWT authentication
- CORS enabled for frontend

# 4. Add new feature
> Add a new endpoint for user profile updates

💬 I'll create a new endpoint. Here's the implementation:

[Code generated for routes/users.py]

# 5. Generate tests
> Generate tests for the new user profile endpoint

[Tests generated]

# 6. Review code
> Review the user profile endpoint for security and best practices

[Security review performed]

# 7. Document
> Generate API documentation for the user profile endpoint

[API documentation generated]

# 8. Git integration
> /git review

📊 Analyzing changes...

**Files Changed:**
- routes/users.py (new)
- tests/test_users.py (new)

**Review:**
✅ Code quality: Good
✅ Tests included: Yes
⚠️ Consider adding rate limiting
💡 Suggestion: Add input validation middleware

> /git commit-msg

💬 Suggested commit message:

feat(api): Add user profile update endpoint

- New PUT /users/profile endpoint
- Validates user authentication
- Updates profile fields: name, email, bio
- Includes comprehensive tests
- Added API documentation

# 9. Create documentation
> Create a README section explaining how to use the profile endpoint

[README section generated]

# 10. Export session
> /export all my-api-development.json

✅ Exported complete session to my-api-development.json
```

---

## Advanced Use Cases

### Example 11: Multi-Agent Analysis

```bash
> /multiagent on

> Compare our authentication implementation with industry best practices
  and suggest improvements

💭 Activating multi-agent system...

**Planner Agent:**
Decomposing task into subtasks:
1. Analyze current authentication implementation
2. Research industry best practices
3. Compare and identify gaps
4. Generate improvement recommendations

**Researcher Agent:**
Researching authentication best practices...
- OWASP Authentication Cheat Sheet
- NIST Digital Identity Guidelines
- OAuth 2.0 and OpenID Connect standards

**Executor Agent:**
Analyzing codebase...
Found authentication code in:
- api/auth.py
- core/security.py
- middleware/auth.py

**Reviewer Agent:**
Comparing implementation with best practices...

💬 **Analysis Results:**

**Current Implementation:**
✅ Password hashing (bcrypt, cost=12)
✅ JWT tokens with expiration
✅ HTTPS enforced
❌ No MFA/2FA
❌ No account lockout
❌ No password complexity requirements
❌ No session management

**Industry Best Practices:**
1. Multi-factor authentication (MFA)
2. Account lockout after failed attempts
3. Password complexity requirements
4. Session management with refresh tokens
5. Security headers (CSP, HSTS, etc.)
6. Rate limiting
7. Audit logging

**Recommended Improvements:**

**Priority 1 (Critical):**
1. Add rate limiting to prevent brute force
2. Implement account lockout (5 failed attempts = 15 min lockout)
3. Add password complexity validation (min 12 chars, mixed case, numbers, symbols)

**Priority 2 (High):**
4. Implement MFA/2FA (TOTP)
5. Add refresh token mechanism
6. Implement security headers

**Priority 3 (Medium):**
7. Add comprehensive audit logging
8. Implement session management
9. Add password expiration policy

**Implementation Plan:**
[Detailed implementation steps for each improvement...]
```

### Example 12: Cross-Session Learning

```bash
# Over multiple sessions, Meton learns patterns

# Session 1
> How do I handle database connections in Python?

💬 [Explanation provided]

# Session 2
> Show me the database connection code

💬 [Code shown]

# Session 3
> /learn analyze

📊 Analyzing usage patterns...

**Detected Patterns:**
1. **Frequent Topic**: Database operations (15 queries)
2. **Common Tools**: codebase_search (database-related)
3. **Success Pattern**: Specific queries get better results

**Generated Insights:**
1. You frequently ask about databases
   - Recommendation: Index database-related documentation
2. Specific queries work better than general ones
   - Recommendation: Use technical terms like "SQLAlchemy" vs "database stuff"

> /learn insights

💡 **Personalized Insights:**

**Insight #1:**
Based on your usage, you work frequently with:
- Database operations
- Authentication systems
- API development

**Recommendations:**
1. Enable `/profile use database-dev` for optimized database queries
2. Index SQLAlchemy documentation for faster lookups
3. Create custom memory: "Always use connection pooling"

> /memory add "Always use SQLAlchemy connection pooling with pool_size=10"

✅ Memory added

# Future sessions automatically use this knowledge
```

---

## Next Steps

For more information:
- **User Guide**: [USER_GUIDE.md](USER_GUIDE.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Start building with Meton today!** 🚀
