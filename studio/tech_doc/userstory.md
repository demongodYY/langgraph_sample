### **User Story**

**As an** online shopper,
**I want to** adjust the quantity of an item in my shopping cart,
**So that** I can ensure my order is accurate before I proceed to payment.

---

### **Acceptance Criteria (AC)**

**Scenario 1: Successfully Increasing Item Quantity**

- **Given** I have an item, 'Premium Coffee Beans', in my shopping cart with a quantity of 2.
- **And** the cart subtotal is calculated based on this quantity.
- **When** I increase the quantity of 'Premium Coffee Beans' to 3.
- **Then** the quantity for 'Premium Coffee Beans' should display as 3.
- **And** the line-item price for 'Premium Coffee Beans' should be recalculated.
- **And** the cart's overall subtotal and total price should update to reflect the change.

**Scenario 2: Successfully Decreasing Item Quantity**

- **Given** I have an item, 'Reusable Filter', in my shopping cart with a quantity of 4.
- **And** the cart subtotal is calculated based on this quantity.
- **When** I decrease the quantity of the 'Reusable Filter' to 1.
- **Then** the quantity for the 'Reusable Filter' should display as 1.
- **And** the cart's overall subtotal and total price should be recalculated and updated.

**Scenario 3: Removing an Item by Setting Quantity to Zero**

- **Given** I have an item, 'Ceramic Mug', in my shopping cart with a quantity of 1.
- **When** I decrease the quantity of the 'Ceramic Mug' to 0.
- **Then** the 'Ceramic Mug' should be completely removed from my shopping cart.
- **And** the cart's total price should be updated accordingly.

**Scenario 4: Attempting to Exceed Available Stock**

- **Given** there are only 5 units of 'Limited Edition Tea' available in stock.
- **And** I have 5 units of 'Limited Edition Tea' in my shopping cart.
- **When** I attempt to increase the quantity to 6.
- **Then** the system should display an error message, such as "Requested quantity exceeds available stock."
- **And** the quantity of 'Limited Edition Tea' in my cart should remain at 5.
