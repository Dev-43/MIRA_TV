# APP_MAP.md (owner: V, due Oct 16)

Fill from the real code. D reads this and must not need to guess.

- Package id: `com.anonymous.MultiTVSample`
- Launch activity: `com.anonymous.MultiTVSample/.MainActivity`
- AVD API level: `34` (Android TV 1080p, API 30–34)
- Node version used: `v24.13.1` (Node.js >= 18 compatible)
- Sample used: `react-native-multi-tv-app-sample` (`expo-multi-tv` workspace app + `shared-ui` package)

## Screens (max 3, lowercase)
| Screen | Rendering file | Notes |
|---|---|---|
| home | `app/packages/shared-ui/src/screens/HomeScreen.tsx` | Main catalog grid with horizontal virtualized rows and hero banner |
| details | `app/packages/shared-ui/src/screens/DetailsScreen.tsx` | Detail view with backdrop, movie metadata, and action buttons |

## Files by role
- Drawer/menu: `app/packages/shared-ui/src/components/CustomDrawerContent.tsx`
- Content cards: `app/packages/shared-ui/src/screens/HomeScreen.tsx` (`MovieItem` inside `SpatialNavigationVirtualizedList`)
- Detail buttons: `app/packages/shared-ui/src/screens/DetailsScreen.tsx` (`FocusablePressable` in `app/packages/shared-ui/src/components/FocusablePressable.tsx`)

## Focus library
- Library: `react-tv-space-navigation` (v6.0.0-beta1)
- Focus component: `SpatialNavigationFocusableView`
- Focus callback prop name: `onFocus` (`onFocus={() => ...}`)
- Select callback prop name: `onSelect` (`onSelect={() => ...}`)
- Container components: `SpatialNavigationRoot`, `DefaultFocus`, `SpatialNavigationNode`
- Back button behaviour: On `details` screen, BACK (KEYCODE_BACK / 4) pops the navigation stack returning to `home`. On `home` screen, pressing LEFT on the leftmost item (`home.card.1`) opens the drawer menu (`CustomDrawerContent`). In the drawer, pressing RIGHT or selecting an item returns focus to `home` content.

## Final element IDs (`<screen>.<region>.<n>`)
- `home.drawer.1`: Home menu item in navigation drawer
- `home.drawer.2`: Explore menu item in navigation drawer
- `home.drawer.3`: TV menu item in navigation drawer
- `home.drawer.settings`: Settings button in navigation drawer footer
- `home.card.1`: Movie card 1 in home highlights row
- `home.card.2`: Movie card 2 in home highlights row
- `home.card.3`: Movie card 3 in home highlights row
- `home.card.4`: Movie card 4 in home highlights row
- `details.btn.play`: "Watch now" primary action button on details screen
- `details.btn.addlist`: "Add to list" secondary action button on details screen
