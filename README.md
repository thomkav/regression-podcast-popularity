# Predicting Podcast Popularity via Storefront Features

I have edited a couple of podcasts and I currently edit the Curious Fox podcast, which offers live recordings of community meetings run by my partner.

The main investigative questions are: 
## Can podcast popularity using topical characteristics of the channel RSS feed?
## Can this analysis be used to recommend front-page / RSS feed presentation strategy for producers?

I'll be scraping the [Castbox](https://castbox.fm/home?country=us) site for individual podcast channel information.
I've chosen this site because it doesn't require login / authentication, and it reveals statistics on the front end.

If I have time, I may try to scrape & download audio samples, to engineer a feature related to audio fidelity.

I'll be looking to predict one of, or an aggregate of, the following:

- On Category Page
- On Top Podcasts
- Sum of Episode Favorites
- Subscriber Count (found on the channel page)
- "Played" count (found on the channel page)

Additionally, I might use the order / index of the podcast on Castbox's site as an additional validation for my prediction.
However, that ranking might be based solely on the total subscriber count, in which case it wouldn't provide much value.
