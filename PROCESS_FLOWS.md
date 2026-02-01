# Holistic Market - Process Flows

This document describes the complete process flows for the Holistic Market (HM) widget system, which enables users to purchase recipe ingredients through integrated grocery delivery services like Amazon Fresh.

## Table of Contents

1. [Widget Embedding Flow](#1-widget-embedding-flow)
2. [Web Scraping Data Collection Flow](#2-web-scraping-data-collection-flow)
3. [Database Synchronization Flow](#3-database-synchronization-flow)
4. [User Checkout Flow](#4-user-checkout-flow)

---

## 1. Widget Embedding Flow

**Purpose**: Describes how Partner Content Providers (PCPs) integrate the Holistic Market widget into their recipe pages.

### Actors
- **Holistic Market**: Provides the widget infrastructure
- **Partner Content Provider (PCP)**: Recipe website owners who embed the widget

### Process Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. PCP adds HM widget to recipe page                                   │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────┐         ┌─────────────────────┐                   │
│  │ Holistic Market │         │ Partner Content     │                   │
│  │                 │         │ Provider            │                   │
│  │  Provide link   │────────▶│  Add widget link    │                   │
│  │  to widget on   │         │  to page HTML code  │                   │
│  │  externally     │         │                     │                   │
│  │  hosted site    │         │                     │                   │
│  └─────────────────┘         └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Process Definition

| Step | Description |
|------|-------------|
| 1. PCP adds HM widget to recipe page | The author of the recipe page on the PCP site adds the code for the Holistic Market widget onto their page |
| 2. Provide link to widget | Holistic Market provides the embed link to the externally hosted widget |
| 3. Add widget link to HTML | PCP integrates the widget link into their page's HTML code |

---

## 2. Web Scraping Data Collection Flow

**Purpose**: Describes how the widget collects recipe and ingredient information from partner recipe pages.

### Components
- **Holistic Market Widget**: Client-side widget embedded on recipe pages
- **Schema Database**: Contains PCP schema definitions for web scraping
- **Local Storage**: Browser-based temporary data storage
- **Content Database**: Stores scraped recipe/ingredient data

### Pre-Process Dependency
- Recipe page 'web scraper' must be available

### Process Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│  2. Web scrape collects 'information' from recipe page                  │
│                                                                         │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────┐                │
│  │   Local     │  │ Holistic Market │  │    Schema    │                │
│  │   Storage   │  │     Widget      │  │   Database   │                │
│  └──────┬──────┘  └────────┬────────┘  └──────┬───────┘                │
│         │                  │                   │                        │
│         │    Recipe page   │                   │                        │
│         │   'information'  │                   │                        │
│         │     is null?     │                   │                        │
│         │◀────────────────▶│                   │                        │
│         │                  │                   │                        │
│         │    ┌─────────────┴──────────┐        │                        │
│         │    │  Widget checks local   │        │                        │
│         │    │       storage          │        │                        │
│         │    └───────────┬────────────┘        │                        │
│         │                │                     │                        │
│         │    ┌───────────▼────────────┐        │                        │
│         │    │ Widget obtains recipe  │        │                        │
│         │    │      page URL          │        │                        │
│         │    └───────────┬────────────┘        │                        │
│         │                │                     │                        │
│         │    ┌───────────▼────────────┐        │                        │
│         │    │   Predefined Process   │        │                        │
│         │    │  (URL trimming, etc.)  │        │                        │
│         │    └───────────┬────────────┘        │                        │
│         │                │                     │                        │
│         │    ┌───────────▼────────────┐        │                        │
│         │    │ Widget obtains recipe  │        │                        │
│         │    │       page PCP         │        │                        │
│         │    └───────────┬────────────┘        │                        │
│         │                │                     │                        │
│         │                │    ┌────────────────▼───────────┐            │
│         │                │    │   Obtain PCP schema        │            │
│         │                │    │      information           │            │
│         │                │    └────────────────┬───────────┘            │
│         │                │                     │                        │
│         │    ┌───────────▼─────────────────────┘                        │
│         │    │ Widget runs 'web scraper'                                │
│         │    │      from schema                                         │
│         │    └───────────┬────────────┐                                 │
│         │                │                                              │
│         │    ┌───────────▼────────────┐                                 │
│         │    │         Data           │                                 │
│         │    └───────────┬────────────┘                                 │
│         │                │                                              │
│         │    ┌───────────▼────────────┐                                 │
│         │    │ Widget sends data to   │                                 │
│         │    │   content database     │                                 │
│         │    └───────────┬────────────┘                                 │
│         │                │                                              │
│         │    ┌───────────▼────────────┐                                 │
│         │    │    Receive Signal      │                                 │
│         │    └────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Widget Process Definition

| Term | Description |
|------|-------------|
| **Identify recipe page** | Determine which recipe page the widget is located on within the PCP site by using the page URL |
| **Store data** | Store the data needed from the "CBDB" (Content Database) for this recipe page by using the page URL as a filter |
| **Predefined Process** | A non-proprietary process used to assist in completing the Widget Process (e.g., trimming URL, converting URL to text) |

---

## 3. Database Synchronization Flow

**Purpose**: Describes how data flows between the Working Database and Content Database, including Amazon Fresh product data synchronization.

### Components
- **Working Database**: Operational database for active widget data
- **Content Database**: Master database for recipe and product information
- **Local Storage**: Temporary client-side storage

### Process Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│  3. Submits request for Amazon Fresh Products                           │
│                                                                         │
│  ┌─────────────────┐              ┌─────────────────┐                  │
│  │    Working      │              │     Content     │                  │
│  │    Database     │              │     Database    │                  │
│  └────────┬────────┘              └────────┬────────┘                  │
│           │                                │                           │
│  ┌────────▼────────┐              ┌────────▼────────┐                  │
│  │ Receives widget │              │  Check Against  │                  │
│  │      data       │              │    Database     │                  │
│  └────────┬────────┘              └────────┬────────┘                  │
│           │                                │                           │
│  ┌────────▼────────┐                       │                           │
│  │Manual Operation │◀──────── No ─────────┤                           │
│  └────────┬────────┘                       │                           │
│           │                       ┌────────▼────────┐                  │
│  ┌────────▼────────┐              │    Decision     │                  │
│  │ Append Amazon   │              │  (Data exists?) │                  │
│  │ Fresh product   │              └────────┬────────┘                  │
│  │      data       │                       │                           │
│  └────────┬────────┘                       │ Yes                       │
│           │                                │                           │
│  ┌────────▼────────┐              ┌────────▼────────┐                  │
│  │      Data       │              │  Amazon Fresh   │                  │
│  └────────┬────────┘              │  product data   │                  │
│           │                       └────────┬────────┘                  │
│  ┌────────▼────────┐                       │                           │
│  │  Amazon Fresh   │◀──────────────────────┘                           │
│  │  Data Package   │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                            │
│  ┌────────▼────────┐                                                   │
│  │   Send Signal   │─────────────────────────▶ Receive Signal          │
│  └─────────────────┘                                                   │
└─────────────────────────────────────────────────────────────────────────┘
```

### Decision Points

| Decision | Yes Path | No Path |
|----------|----------|---------|
| Recipe page 'information' is null? | Widget obtains recipe page URL | Use cached data |
| Amazon Fresh product data is null? | Query Amazon Fresh API | Use existing data package |
| Check Against Database | Use existing data | Manual operation to append data |

---

## 4. User Checkout Flow

**Purpose**: Describes the end-to-end process when a user purchases recipe ingredients through the Holistic Market widget.

### Actors
- **User**: End user purchasing ingredients
- **Holistic Market Widget**: The embedded checkout interface
- **Amazon Fresh (or Other)**: Grocery delivery fulfillment service

### Process Steps

```
┌─────────────────────────────────────────────────────────────────────────┐
│  User Checkout Process                                                  │
│                                                                         │
│  ┌─────────────────┐         ┌─────────────────────┐                   │
│  │      User       │         │  Holistic Market    │                   │
│  │                 │         │      Widget         │                   │
│  └────────┬────────┘         └──────────┬──────────┘                   │
│           │                             │                              │
│  ┌────────▼────────┐                    │                              │
│  │ User clicks on  │                    │                              │
│  │ HM Widget to    │                    │                              │
│  │ purchase recipe │                    │                              │
│  │   ingredients   │                    │                              │
│  └────────┬────────┘                    │                              │
│           │                             │                              │
│           │              ┌──────────────▼──────────────┐               │
│           │              │  Widget prompts user for    │               │
│           │              │  check out information      │               │
│           │              └──────────────┬──────────────┘               │
│           │                             │                              │
│  ┌────────▼──────────────────┐          │                              │
│  │  User provides:           │          │                              │
│  │  1. Email                 │          │                              │
│  │  2. Name                  │          │                              │
│  │  3. Address               │          │                              │
│  │  4. Phone number          │──────────┤                              │
│  │  5. Payment Method        │          │                              │
│  └───────────────────────────┘          │                              │
│                                         │                              │
│           ┌─────────────────────────────▼────────────────────────┐     │
│           │               User Information                       │     │
│           └─────────────────────────────┬────────────────────────┘     │
│                                         │                              │
│           ┌─────────────────────────────▼────────────────────────┐     │
│           │    5. Widget "submits order to Amazon Fresh"         │     │
│           └─────────────────────────────┬────────────────────────┘     │
│                                         │                              │
└─────────────────────────────────────────┼──────────────────────────────┘
                                          │
┌─────────────────────────────────────────┼──────────────────────────────┐
│  Order Processing                       │                              │
│                                         │                              │
│  ┌─────────────────┐  ┌─────────────────▼───┐  ┌────────────────────┐  │
│  │ Holistic Market │  │   Local Storage     │  │   Amazon Fresh     │  │
│  │     Widget      │  │                     │  │     or Other       │  │
│  └────────┬────────┘  └──────────┬──────────┘  └─────────┬──────────┘  │
│           │                      │                       │             │
│  ┌────────▼────────┐             │                       │             │
│  │ Widget accesses │             │                       │             │
│  │  local storage  │◀────────────┘                       │             │
│  └────────┬────────┘                                     │             │
│           │           ┌──────────────────┐               │             │
│           │           │  Amazon Fresh    │               │             │
│           │           │  product data    │               │             │
│           │           └────────┬─────────┘               │             │
│           │                    │                         │             │
│  ┌────────▼────────────────────▼────────┐                │             │
│  │              Merge                    │                │             │
│  └──────────────────┬───────────────────┘                │             │
│                     │                                    │             │
│           ┌─────────▼─────────┐                          │             │
│           │  Amazon Fresh     │                          │             │
│           │  Data Package     │                          │             │
│           └─────────┬─────────┘                          │             │
│                     │                                    │             │
│           ┌─────────▼─────────┐       ┌──────────────────▼───────────┐ │
│           │      Order        │──────▶│      Order received          │ │
│           └─────────┬─────────┘       └──────────────────┬───────────┘ │
│                     │                                    │             │
│           ┌─────────▼─────────┐       ┌──────────────────▼───────────┐ │
│           │    Order Info     │──────▶│  Process Order and Ship     │ │
│           └─────────┬─────────┘       │      to Customer            │ │
│                     │                 └──────────────────────────────┘ │
│  ┌──────────────────▼───────────────┐                                  │
│  │  6. Widget "send users           │                                  │
│  │     confirmation email"          │                                  │
│  └──────────────────────────────────┘                                  │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### Checkout Steps Summary

| Step | Action | Actor |
|------|--------|-------|
| 1 | User clicks on HM Widget to purchase recipe ingredients | User |
| 2 | Widget prompts user for checkout information | Widget |
| 3 | User provides email, name, address, phone number, payment method | User |
| 4 | User information sent to widget | System |
| 5 | Widget submits order to Amazon Fresh | Widget |
| 6 | Widget accesses local storage and merges with Amazon Fresh data | Widget |
| 7 | Order created and sent to Amazon Fresh | System |
| 8 | Order received and processed | Amazon Fresh |
| 9 | Order shipped to customer | Amazon Fresh |
| 10 | Widget sends confirmation email to user | Widget |

---

## Data Flow Summary

### Key Data Objects

| Object | Description |
|--------|-------------|
| **User Information** | Email, name, address, phone, payment method |
| **Amazon Fresh Data Package** | Product data merged from local storage and Amazon Fresh API |
| **Order** | Complete order information sent to fulfillment |
| **Order Info** | Tracking and shipping details |

### Integration Points

1. **Widget ↔ Local Storage**: Caching recipe and product data
2. **Widget ↔ Schema Database**: Retrieving PCP-specific scraping schemas
3. **Widget ↔ Content Database**: Storing and retrieving recipe data
4. **Widget ↔ Working Database**: Operational data management
5. **Widget ↔ Amazon Fresh API**: Product data and order submission
6. **Widget ↔ User**: Checkout interface and confirmations

---

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Partner Content Provider                        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                        Recipe Page                                │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │              Holistic Market Widget (Embedded)              │  │  │
│  │  └────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Holistic Market Backend                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │    Schema      │  │    Content     │  │      Working           │   │
│  │   Database     │  │   Database     │  │      Database          │   │
│  └────────────────┘  └────────────────┘  └────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    Fulfillment Partners                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────┐   │
│  │  Amazon Fresh  │  │   Instacart    │  │       Others           │   │
│  └────────────────┘  └────────────────┘  └────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Glossary

| Term | Definition |
|------|------------|
| **HM** | Holistic Market |
| **PCP** | Partner Content Provider - a website that hosts recipe content and embeds the HM widget |
| **CBDB** | Content Database |
| **Widget** | The embedded Holistic Market interface on partner recipe pages |
| **Predefined Process** | Non-proprietary helper processes (URL trimming, text conversion, etc.) |
| **Amazon Fresh Data Package** | Combined product and availability data from Amazon Fresh |
