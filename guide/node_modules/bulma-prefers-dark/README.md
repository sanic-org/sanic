# bulma-prefers-dark

![Safari screenshot](.github/safari-screenshot.png)

A Bulma extension that adds support for the `prefers-color-scheme: dark` media query

[![npm](https://img.shields.io/npm/v/bulma-prefers-dark.svg)](https://www.npmjs.com/package/bulma-prefers-dark)
[![npm](https://img.shields.io/npm/dm/bulma-prefers-dark.svg)](https://www.npmjs.com/package/bulma-prefers-dark)

## Installation

```
npm install bulma-prefers-dark
... Or ...
yarn add bulma-prefers-dark
```

## Usage

This extension works as-is in combination with Bulma by adding an alternative dark theme via the `@media (prefers-color-scheme: dark)` [media query](https://caniuse.com/#search=prefers-color-scheme).

Include it in your SaSS pipeline after you've included Bulma and you're good to go:

```scss
@import "../../node_modules/bulma/bulma.sass";
@import "../../bulma-prefers-dark/bulma-prefers-dark.sass";
```

Alternatively include it in your HTML via unpkg:

```html
<link rel="stylesheet" type="text/css" href="https://unpkg.com/bulma-prefers-dark" />
```

<!-- TODO: Add example sites -->

## Copyright & License

Code copyright 2019 James Loh. Code released under the [MIT license](LICENSE).
