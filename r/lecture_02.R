library(tsibble)
library(tsibbledata)
library(dplyr)
library(ggplot2)
library(feasts)
library(readxl)
library(feasts)

tute1 <- read.csv2(".data/tute1.csv", header=TRUE, sep = ",")
tute1 <- tute1 |> 
  mutate(Quarter = as.Date(Quarter, format="%Y-%m-%d")) |> 
  mutate(Sales = as.numeric(Sales)) |>
  mutate(AdBudget = as.numeric(AdBudget)) |>
  mutate(GDP = as.numeric(GDP))
  

tute1_tsibble <- tute1 |> as_tsibble(index = Quarter)

# Ex 1

# Sales
tute1_tsibble |> autoplot(Sales) +
  labs(title = "Sales Over Time (autoplot)", x = "Quarter", y = "Sales")

ggplot(tute1_tsibble, aes(x = Quarter, y = Sales)) +
  geom_line() +
  labs(title = "Sales Over Time (ggplot)", x = "Quarter", y = "Sales")

ggplot(tute1_tsibble, aes(x = Quarter, y = Sales)) +
  geom_point() +
  labs(title = "Scatterplot of Sales over Time", x = "Quarter", y = "Sales")


# AdBudget
tute1_tsibble |> autoplot(AdBudget) + 
  labs(title = "AdBudget Over Time (autoplot)", x = "Quarter", y = "AdBudget")

ggplot(tute1_tsibble, aes(x = Quarter, y = AdBudget)) +
  geom_line() +
  labs(title = "AdBudget Over Time (ggplot)", x = "Quarter", y = "AdBudget")

ggplot(tute1_tsibble, aes(x = Quarter, y = AdBudget)) +
  geom_point() +
  labs(title = "Scatterplot of AdBudget over Time", x = "Quarter", y = "AdBudget")

# GDP
tute1_tsibble |> autoplot(GDP) + 
  labs(title = "GDP Over Time (autoplot)", x = "Quarter", y = "GDP")

ggplot(tute1_tsibble, aes(x = Quarter, y = GDP)) +
  geom_line() +
  labs(title = "GDP Over Time (ggplot)", x = "Quarter", y = "GDP")


# Ex 2
tourism_tsibble <- read_excel(".data/tourism.xlsx") |>
  mutate(Quarter = as.Date(Quarter, format="%Y-%m-%d")) |>
  mutate(Trips = as.numeric(Trips))
  
# AVerage by Region and Purpose
avg_by_region_purpose <- tourism_tsibble |> 
  group_by(Region, Purpose) |>
  summarise(AvgTrips = mean(Trips)) |>
  arrange(desc(AvgTrips))

avg_by_region_purpose

# Total Trips by State
total_by_state <- tourism_tsibble |>
  group_by(State) |>
  summarise(TotalTrips = sum(Trips)) |>
  arrange(desc(TotalTrips))

total_by_state

# Ex 3
set.seed(1122334455)
aus_retail_series <- aus_retail |>
  filter(`Series ID` == sample(aus_retail$`Series ID`,1))

# autoplot
aus_retail_series |> autoplot(Turnover)

# gg_season
aus_retail_series |> gg_season(Turnover)

# gg_subseries
aus_retail_series |> gg_subseries(Turnover)

# gg_lag
aus_retail_series |> gg_lag(Turnover, lags = 1:12)

# ACF
aus_retail_series |> ACF(Turnover, lag_max = 48) |> autoplot()

# Ex 4

# Bricks (aus_production)
aus_production |> autoplot(Bricks) + geom_point()

aus_production |> gg_season(Bricks)

aus_production |> gg_subseries(Bricks)

aus_production |> gg_lag(Bricks, geom = "point")

aus_production |> ACF(Bricks) |> autoplot()

# Ex 5
# 1 : B
# 2 : A
# 3 : D
# 4 : C
