# Notify Me When Available

Odoo 18 module for personal stock availability reminders.

## Usage

1. Sign in as an internal Sales user and open **Notify Me > My Reminders**.
2. Create a reminder with a product, warehouse and quantity in the product's stock unit.
3. Open the saved reminder and select **Check Now**.
4. When the warehouse has enough unreserved stock, the reminder becomes **Notified**
   and an activity is assigned to its requester. Otherwise it remains **Waiting**.

Sales users can access their own reminders in their active companies. Cancel a
waiting reminder and create a new one to change its product, warehouse or quantity.
No stock quantities, reservations, sales orders or purchase orders are changed.

## Scheduled checks

The scheduled action **Notify Me: Check Stock Availability** is disabled on installation.
Use **Check Now** for the first demonstration. After acceptance, an administrator can
enable the scheduled action. Its interval is five minutes; actual execution depends
on the hosting scheduler. Each run checks at most 200 waiting reminders, checking
the least recently checked reminders first.

## Trial status

Prepared for an Odoo 18 staging trial. Installation and user acceptance remain pending.
Python syntax, XML structure and package references are checked before publication;
these checks do not replace an Odoo installation test.

## Verification

- Below the requested quantity: a check leaves the reminder waiting, with no activity.
- Enough unreserved stock: one activity is assigned and the reminder becomes notified.
- Checking the same notified reminder again creates no additional activity.
- A cancelled reminder creates no activity.
- Another salesperson cannot read or change someone else's reminder.
- A warehouse from another company and a non-positive quantity are rejected.

Availability is a point-in-time check, not a reservation or a promise of delivery.
Removing the temporary files from an installed database is not an uninstall. Uninstall
the module through Apps before removing its files if abandoning the trial. Changes
made only in an Odoo.sh build may be lost when that build is replaced.
