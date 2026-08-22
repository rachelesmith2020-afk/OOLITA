# OOLITA Stripe checkout plan

OOLITA uses one live Stripe account and two underlying physical products, each with two locale-specific one-time prices and Payment Links.

| Site route | Product | Currency | Price | Stripe Payment Link |
| --- | --- | --- | --- | --- |
| `/ediciones/libro/` | OOLITA · libro bilingüe | EUR | TBD | TBD |
| `/en/editions/book/` | OOLITA · bilingual book | GBP | TBD | TBD |
| `/ediciones/camiseta/` | OOLITA · primera edición textil | EUR | TBD | TBD |
| `/en/editions/t-shirt/` | OOLITA · first textile edition | GBP | TBD | TBD |

The Spanish and English routes are not separate inventory items: they point to the same underlying book or textile product. Currency and checkout link differ by locale. Until prices are decided, the public site remains in email-interest mode and must not display a fake Buy button.
