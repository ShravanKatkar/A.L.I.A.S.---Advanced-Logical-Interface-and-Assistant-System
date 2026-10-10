import { initializeApp, getApps, getApp } from 'firebase/app';
import { 
  getAuth, 
  GoogleAuthProvider, 
  signInWithPopup, 
  signInWithEmailAndPassword, 
  createUserWithEmailAndPassword, 
  updateProfile, 
  signOut as firebaseSignOut 
} from 'firebase/auth';

/**
 * Retrieves the currently active Firebase configuration.
 * Checks in order:
 * 1. Saved config in localStorage
 * 2. Vite environment variables (VITE_FIREBASE_*)
 */
export function getFirebaseConfig() {
  const localConfigStr = localStorage.getItem('alias_firebase_config');
  if (localConfigStr) {
    try {
      const parsed = JSON.parse(localConfigStr);
      if (parsed && parsed.apiKey && parsed.projectId) {
        return parsed;
      }
    } catch (e) {
      console.warn('Failed to parse saved Firebase config from localStorage:', e);
    }
  }

  // Fallback to Vite env variables
  const envConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY || '',
    authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || '',
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || '',
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || '',
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || '',
    appId: import.meta.env.VITE_FIREBASE_APP_ID || '',
    measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID || '',
  };

  if (envConfig.apiKey && envConfig.projectId) {
    return envConfig;
  }

  return null;
}

/**
 * Checks whether Firebase has sufficient valid credentials to initialize.
 */
export function isFirebaseConfigured(config = null) {
  const cfg = config || getFirebaseConfig();
  return Boolean(cfg && cfg.apiKey && cfg.projectId && cfg.appId);
}

/**
 * Saves Firebase configuration into localStorage and reinitializes the app.
 */
export function saveFirebaseConfig(config) {
  if (!config || !config.apiKey) {
    throw new Error('Invalid Firebase configuration object.');
  }
  localStorage.setItem('alias_firebase_config', JSON.stringify(config));
  return getFirebaseAuth(config, true);
}

/**
 * Gets or initializes the Firebase App instance.
 */
export function getFirebaseApp(customConfig = null, forceReinit = false) {
  const config = customConfig || getFirebaseConfig();
  if (!config || !config.apiKey) {
    throw new Error('Firebase configuration is not set. Please configure your Firebase project credentials.');
  }

  if (getApps().length > 0) {
    if (forceReinit) {
      const existing = getApp();
      // Firebase doesn't allow direct reinit of default app without delete, so we use it or get existing
      return existing;
    }
    return getApp();
  }

  return initializeApp(config);
}

/**
 * Gets the FirebaseAuth instance.
 */
export function getFirebaseAuth(customConfig = null, forceReinit = false) {
  const app = getFirebaseApp(customConfig, forceReinit);
  return getAuth(app);
}

/**
 * Sign in with Google using Firebase Popup.
 */
export async function signInWithGoogleFirebase(customConfig = null) {
  const auth = getFirebaseAuth(customConfig);
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: 'select_account' });

  const result = await signInWithPopup(auth, provider);
  const user = result.user;
  const idToken = await user.getIdToken();

  return {
    user,
    idToken,
    email: user.email,
    name: user.displayName || user.email.split('@')[0],
    picture: user.photoURL || '',
    uid: user.uid,
    provider: 'google.com'
  };
}

/**
 * Sign in with Email and Password using Firebase.
 */
export async function signInWithEmailFirebase(email, password, customConfig = null) {
  const auth = getFirebaseAuth(customConfig);
  const result = await signInWithEmailAndPassword(auth, email.trim(), password);
  const user = result.user;
  const idToken = await user.getIdToken();

  return {
    user,
    idToken,
    email: user.email,
    name: user.displayName || user.email.split('@')[0],
    picture: user.photoURL || '',
    uid: user.uid,
    provider: 'password'
  };
}

/**
 * Register a new user with Email and Password using Firebase.
 */
export async function signUpWithEmailFirebase(name, email, password, customConfig = null) {
  const auth = getFirebaseAuth(customConfig);
  const result = await createUserWithEmailAndPassword(auth, email.trim(), password);
  const user = result.user;

  if (name && name.trim()) {
    try {
      await updateProfile(user, { displayName: name.trim() });
    } catch (e) {
      console.warn('Could not update Firebase user displayName:', e);
    }
  }

  const idToken = await user.getIdToken();

  return {
    user,
    idToken,
    email: user.email,
    name: name?.trim() || user.displayName || user.email.split('@')[0],
    picture: user.photoURL || '',
    uid: user.uid,
    provider: 'password'
  };
}

/**
 * Sign out of Firebase session.
 */
export async function signOutFirebase() {
  try {
    const auth = getFirebaseAuth();
    await firebaseSignOut(auth);
  } catch (e) {
    // Ignore error if auth was not initialized
  }
}

/**
 * Formats Firebase error codes into helpful user messages.
 */
export function formatFirebaseError(error) {
  if (!error) return 'Authentication failed.';
  const code = error.code || '';

  switch (code) {
    case 'auth/invalid-credential':
    case 'auth/wrong-password':
    case 'auth/user-not-found':
      return 'Invalid email or password.';
    case 'auth/email-already-in-use':
      return 'This email is already in use. Please sign in instead.';
    case 'auth/weak-password':
      return 'Password should be at least 6 characters.';
    case 'auth/invalid-email':
      return 'Please enter a valid email address.';
    case 'auth/popup-closed-by-user':
      return 'Google sign-in popup was closed before completion.';
    case 'auth/cancelled-popup-request':
      return 'Sign-in was cancelled.';
    case 'auth/popup-blocked':
      return 'Sign-in popup was blocked by browser. Please allow popups for this site.';
    case 'auth/network-request-failed':
      return 'Network error. Please check your internet connection.';
    case 'auth/operation-not-allowed':
      return 'This sign-in method is not enabled in your Firebase Console (Authentication > Sign-in method).';
    default:
      return error.message || 'Firebase authentication failed.';
  }
}
