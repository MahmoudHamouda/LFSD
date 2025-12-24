import { NavigateFunction } from 'react-router-dom';

/**
 * Redirects the user to the Profile page with a specific tab and anchor section.
 * Enforces the Single Interaction Contract: All management lives in Profile.
 *
 * @param navigate - React Router navigate function
 * @param tab - The target Profile tab ('financial', 'health', 'time')
 * @param anchor - The specific section ID to scroll to (e.g., 'connections-health')
 */
export const redirectToProfile = (
  navigate: NavigateFunction,
  tab: 'financial' | 'health' | 'time' | 'account',
  anchor?: string
) => {
  let url = `/profile?tab=${tab}`;
  if (anchor) {
    url += `#${anchor}`;
  }
  navigate(url);
};
