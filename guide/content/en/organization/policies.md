# Policies

## Versioning

Sanic uses [calendar versioning](https://calver.org/), aka "calver". To be more specific, the pattern follows:

```
YY.MM.MICRO
```

Generally, versions are referred to in their ``YY.MM`` form. The `MICRO` number indicates an incremental patch version, starting at `0`.

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

| Version | LTS           | Supported |
| ------- | ------------- | --------- |
| 23.6    |               | ✅        |
| 23.3    |               | ⚪        |
| 22.12   | until 2024-12 | ☑️         |
| 22.9    |               | ⚪        |
| 22.6    |               | ⚪        |
| 22.3    |               | ⚪        |
| 21.12   | until 2023-12 | ☑️         |
| 21.9    |               | ⚪        |
| 21.6    |               | ⚪        |
| 21.3    |               | ⚪        |
| 20.12   |               | ⚪        |
| 20.9    |               | ⚪        |
| 20.6    |               | ⚪        |
| 20.3    |               | ⚪        |
| 19.12   |               | ⚪        |
| 19.9    |               | ⚪        |
| 19.6    |               | ⚪        |
| 19.3    |               | ⚪        |
| 18.12   |               | ⚪        |
| 0.8.3   |               | ⚪        |
| 0.7.0   |               | ⚪        |
| 0.6.0   |               | ⚪        |
| 0.5.4   |               | ⚪        |
| 0.4.1   |               | ⚪        |
| 0.3.1   |               | ⚪        |
| 0.2.0   |               | ⚪        |
| 0.1.9   |               | ⚪        |

☑️ = security fixes 
✅ = full support
⚪ = no support

## Deprecation

Before a feature is deprecated, or breaking changes are introduced into the API, it shall be publicized and shall appear with deprecation warnings through two release cycles. No deprecations shall be made in an LTS release.

Breaking changes or feature removal may happen outside of these guidelines when absolutely warranted. These circumstances should be rare. For example, it might happen when no alternative is available to curtail a major security issue.
