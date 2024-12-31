# Policies

## Versioning

Sanic uses [calendar versioning](https://calver.org/), aka "calver". To be more specific, the pattern follows:

```
YY.MM.MICRO
```

Generally, versions are referred to in their ``YY.MM`` form. The `MICRO` number indicates an incremental patch version, starting at `0`.

## Reporting a Vulnerability

If you discover a security vulnerability, we ask that you **do not** create an issue on GitHub. Instead, please [send a message to the core-devs](https://community.sanicframework.org/g/core-devs) on the community forums. Once logged in, you can send a message to the core-devs by clicking the message button.

Alternatively, you can send a private message to Adam Hopkins on Discord. Find him on the [Sanic discord server](https://discord.gg/FARQzAEMAA).

This will help to not publicize the issue until the team can address it and resolve it.

## Release Schedule

There are four (4) scheduled releases per year: March, June, September, and December. Therefore, there are four (4) released versions per year: `YY.3`, `YY.6`, `YY.9`, and `YY.12`. 

This release schedule provides:

- a predictable release cadence,
- relatively short development windows allowing features to be regularly released,
- controlled [deprecations](#deprecation), and
- consistent stability with a yearly LTS.

We also use the yearly release cycle in conjunction with our governance model, covered by the [S.C.O.P.E.](./scope.md)

### Long term support v Interim releases

Sanic releases a long term support release (aka "LTS") once a year in December. The LTS releases receive bug fixes and security updates for **24 months**. Interim releases throughout the year occur every three months, and are supported until the subsequent release.

| Version | Release    | LTS           | Supported       |
|---------|------------|---------------|-----------------|
| 24.12   | 2024-12-31 | until 2026-12 | ✅              |
| 24.6    | 2024-06-30 |               | ⚪              |
| 23.12   | 2023-12-31 | until 2025-12 | ☑️              |
| 23.6    | 2023-07-25 |               | ⚪              |
| 23.3    | 2023-03-26 |               | ⚪              |
| 22.12   | 2022-12-27 |               | ☑️              |
| 22.9    | 2022-09-29 |               | ⚪              |
| 22.6    | 2022-06-30 |               | ⚪              |
| 22.3    | 2022-03-31 |               | ⚪              |
| 21.12   | 2021-12-26 |               | ⚪              |
| 21.9    | 2021-09-30 |               | ⚪              |
| 21.6    | 2021-06-27 |               | ⚪              |
| 21.3    | 2021-03-21 |               | ⚪              |
| 20.12   | 2020-12-29 |               | ⚪              |
| 20.9    | 2020-09-30 |               | ⚪              |
| 20.6    | 2020-06-28 |               | ⚪              |
| 20.3    | 2020-05-14 |               | ⚪              |
| 19.12   | 2019-12-27 |               | ⚪              |
| 19.9    | 2019-10-12 |               | ⚪              |
| 19.6    | 2019-06-21 |               | ⚪              |
| 19.3    | 2019-03-23 |               | ⚪              |
| 18.12   | 2018-12-27 |               | ⚪              |
| 0.8.3   | 2018-09-13 |               | ⚪              |
| 0.7.0   | 2017-12-06 |               | ⚪              |
| 0.6.0   | 2017-08-03 |               | ⚪              |
| 0.5.4   | 2017-05-09 |               | ⚪              |
| 0.4.1   | 2017-02-28 |               | ⚪              |
| 0.3.1   | 2017-02-09 |               | ⚪              |
| 0.2.0   | 2017-01-14 |               | ⚪              |
| 0.1.9   | 2016-12-25 |               | ⚪              |
| 0.1.0   | 2016-10-16 |               | ⚪              |

☑️ = security fixes  
✅ = full support  
⚪ = no support

## Deprecation

Before a feature is deprecated, or breaking changes are introduced into the API, it shall be publicized and shall appear with deprecation warnings through two release cycles. No deprecations shall be made in an LTS release.

Breaking changes or feature removal may happen outside of these guidelines when absolutely warranted. These circumstances should be rare. For example, it might happen when no alternative is available to curtail a major security issue.
