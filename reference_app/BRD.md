# Reference Shop — Business Requirements Document (BRD)

This document describes, in plain language, the intended behavior of the reference shop
application. It is written the way a QA lead would capture business requirements: it says what
the shop should do for its users, not how the code is built. It is the human-readable statement
of intended behavior that later phases diff against the shipped code to synthesize and maintain
tests. It is deliberately free of source listings, API schemas, and test scripts.

## Overview

The reference shop is a small online store. A signed-in customer can browse a catalog of
products, add products to a personal cart, and check out to place an order. Orders can be
retrieved afterward and reflect exactly what was purchased and what it cost. Everything a
customer does — viewing products, managing the cart, checking out, and looking up orders —
requires the customer to be authenticated first.

## Authentication

The shop is private: a user must sign in with credentials before they can use any part of it.
Access is granted only when the supplied credentials match a known account. When a user provides
valid credentials, the shop accepts the request and lets the user proceed to browse and shop.
When credentials are missing, or when they are invalid, incorrect, or belong to no known account,
the shop rejects the request as unauthorized and does not reveal any shop data. In short, valid
credentials grant access and invalid or missing credentials are denied.

## Products

Once signed in, the customer can browse the shop's catalog of products. The catalog is a list of
the products the shop offers for sale. Each product carries at least a human-readable name and a
price, so the customer can see what an item is and what it costs before deciding to buy it. The
catalog the customer browses is stable and consistent: the same products, with the same names and
the same prices, are presented on every visit.

## Cart and add-to-cart

Each signed-in customer has their own cart, and a customer's cart is private to that customer.
Starting out, the cart is empty. A customer builds up an order by adding products to the cart,
choosing a product and a quantity. When a customer adds a product that is already in the cart, the
requested quantity is added to the quantity already there rather than replacing it: the line's
quantity is cumulative. For example, adding two of an item and then adding three more of the same
item leaves five of that item in the cart — the new amount increases the existing quantity instead
of resetting it back to a single unit. Attempts to add a product that does not exist in the catalog
are refused and leave the cart unchanged.

## Checkout

When a customer is ready to buy, they check out. Checking out a cart that holds at least one item
turns the cart's contents into a confirmed order for that customer, and the cart is cleared so the
customer can start a fresh cart afterward. Checking out an empty cart is not allowed: the shop
rejects an attempt to check out with nothing in the cart and no order is created. In other words,
an order can only be created from a non-empty cart.

## Orders

Checking out creates an order, and that order can be retrieved afterward for review or
confirmation. When a customer looks up one of their orders, the shop returns the order and it
reflects the items that were purchased — the products and the quantity of each — along with the
amount charged. An order that does not exist cannot be retrieved. This lets a customer view a
confirmation of what they bought after the purchase is complete.

## Order total

The order total is the amount the customer pays. It is computed per line: for each product line in
the cart, the shop multiplies that product's price by the quantity of that product, and the total
is the sum of those per-line amounts across every line. Because the order is created from the cart
at checkout, the order's total equals the cart total at the moment of checkout — the total shown on
the placed order is exactly the sum, over each line, of price times quantity.
