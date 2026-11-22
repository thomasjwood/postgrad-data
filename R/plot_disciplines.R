# Faceted time series: graduate students per social science discipline, 1975-2025.
# Uses the harmonized political science series (output/polisci_harmonized.csv) and the
# discipline table (output/social_science_grad_students_wide.csv). Run from the repo root:
#   Rscript R/plot_disciplines.R

library(dplyr)
library(tidyr)
library(readr)
library(ggplot2)

wide <- read_csv("output/social_science_grad_students_wide.csv", show_col_types = FALSE)
harm <- read_csv("output/polisci_harmonized.csv", show_col_types = FALSE)

# fields carved out of NSF's pre-2017 political science code: estimated before 2017, reported from 2017
split_fields <- harm |>
  select(year,
         `Political science` = political_science,
         `International relations` = international_relations,
         `Public policy` = public_policy,
         `Public administration` = public_administration) |>
  pivot_longer(-year, names_to = "field", values_to = "n") |>
  mutate(status = if_else(year <= 2016, "Estimated from IPEDS split", "Reported by NSF"),
         # the 1980 IPEDS file (HEGIS codes) has no public policy category, so the split gives 0 for 1972-77
         n = if_else(field == "Public policy" & n == 0, NA_real_, n))

# where the estimated and reported segments meet, repeat 2017 in the estimated series
# so the dashed line runs into the solid one with no gap
bridge <- split_fields |>
  filter(year == 2017, field != "Public administration") |>
  mutate(status = "Estimated from IPEDS split")

# criminology/criminal justice is left out: it sat inside "other social sciences" until 2017 and
# criminology only got its own code in 2020, so its series is short and broken
reported <- wide |>
  select(year, Economics, `Agricultural economics`, Sociology, Anthropology, Geography,
         Linguistics, Psychology) |>
  pivot_longer(-year, names_to = "field", values_to = "n") |>
  mutate(status = "Reported by NSF")

field_order <- c("Political science", "International relations", "Public policy", "Public administration",
                 "Economics", "Agricultural economics", "Sociology", "Anthropology",
                 "Geography", "Linguistics", "Psychology")

d <- bind_rows(split_fields, bridge, reported) |>
  filter(year >= 1975, !is.na(n)) |>   # 1972-74 surveyed fewer institutions
  mutate(k = n / 1000,
         field = factor(field, levels = field_order))

# label bubbles: first and last point of each discipline
lab_pts <- d |>
  distinct(field, year, .keep_all = TRUE) |>
  group_by(field) |>
  filter(year == min(year) | year == max(year)) |>
  ungroup() |>
  mutate(lab = if_else(k >= 10, sprintf("%.0f", k), sprintf("%.1f", k)))  # whole numbers fit the bubble

line_col <- "#2b5c8a"

p <- ggplot(d, aes(year, k)) +
  geom_line(aes(linetype = status, group = interaction(field, status)),
            colour = line_col, linewidth = .35) +
  geom_point(data = lab_pts, shape = 21, fill = "white", colour = line_col, size = 6.5, stroke = .4) +
  geom_point(data = lab_pts, shape = 21, fill = "white", colour = "white", size = 6, stroke = 0) +
  geom_text(data = lab_pts, aes(label = lab), colour = line_col, size = 2.4, family = "Public Sans") +
  facet_wrap(~field, ncol = 4) +
  scale_x_continuous(breaks = c(1980, 2000, 2020), expand = expansion(mult = .06)) +
  scale_y_continuous(expand = expansion(mult = .18)) +
  scale_linetype_manual(values = c("Estimated from IPEDS split" = "22", "Reported by NSF" = "solid"),
                        name = NULL) +
  labs(title = "Graduate students by social science discipline, 1975–2025",
       subtitle = "Thousands enrolled each fall, master's and doctoral",
       x = NULL, y = NULL,
       caption = "Source: NSF/NCSES Survey of Graduate Students and Postdoctorates in Science and Engineering; IPEDS Completions") +
  theme_minimal(base_family = "Public Sans", base_size = 10) +
  theme(panel.background = element_rect(fill = "grey95", colour = NA),
        panel.grid = element_blank(),
        strip.background = element_rect(fill = "grey95", colour = NA),
        plot.title = element_text(face = "bold"),
        plot.title.position = "plot",
        plot.caption.position = "plot",
        plot.caption = element_text(hjust = 0, colour = "grey35", size = rel(.75)),
        legend.position = "top",
        legend.justification = "left",
        legend.key.width = unit(1.6, "lines"))

dir.create("figures", showWarnings = FALSE)
ggsave("figures/grad_students_by_discipline.png", p, width = 10, height = 7.2, dpi = 300,
       device = ragg::agg_png, bg = "white")
