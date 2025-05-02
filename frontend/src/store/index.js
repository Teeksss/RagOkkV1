import { createContext, useContext, useReducer } from 'react';

// İlk state
const initialState = {
  theme: 'light',
  sidebarOpen: false,
  notifications: [],
  systemMessages: [],
  searchFilters: {},
  preferences: {
    itemsPerPage: 10,
    showHelpTips: true,
    autoRefresh: false
  }
};

// Action türleri
export const ACTIONS = {
  SET_THEME: 'SET_THEME',
  TOGGLE_SIDEBAR: 'TOGGLE_SIDEBAR',
  ADD_NOTIFICATION: 'ADD_NOTIFICATION',
  REMOVE_NOTIFICATION: 'REMOVE_NOTIFICATION',
  CLEAR_NOTIFICATIONS: 'CLEAR_NOTIFICATIONS',
  ADD_SYSTEM_MESSAGE: 'ADD_SYSTEM_MESSAGE',
  REMOVE_SYSTEM_MESSAGE: 'REMOVE_SYSTEM_MESSAGE',
  SET_SEARCH_FILTERS: 'SET_SEARCH_FILTERS',
  CLEAR_SEARCH_FILTERS: 'CLEAR_SEARCH_FILTERS',
  UPDATE_PREFERENCES: 'UPDATE_PREFERENCES'
};

// Reducer fonksiyonu
const reducer = (state, action) => {
  switch (action.type) {
    case ACTIONS.SET_THEME:
      return { ...state, theme: action.payload };
    
    case ACTIONS.TOGGLE_SIDEBAR:
      return { ...state, sidebarOpen: action.payload !== undefined ? action.payload : !state.sidebarOpen };
    
    case ACTIONS.ADD_NOTIFICATION:
      return {
        ...state,
        notifications: [...state.notifications, { id: Date.now(), ...action.payload }]
      };
    
    case ACTIONS.REMOVE_NOTIFICATION:
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload)
      };
    
    case ACTIONS.CLEAR_NOTIFICATIONS:
      return { ...state, notifications: [] };
    
    case ACTIONS.ADD_SYSTEM_MESSAGE:
      return {
        ...state,
        systemMessages: [...state.systemMessages, { id: Date.now(), ...action.payload }]
      };
    
    case ACTIONS.REMOVE_SYSTEM_MESSAGE:
      return {
        ...state,
        systemMessages: state.systemMessages.filter(m => m.id !== action.payload)
      };
    
    case ACTIONS.SET_SEARCH_FILTERS:
      return { ...state, searchFilters: { ...state.searchFilters, ...action.payload } };
    
    case ACTIONS.CLEAR_SEARCH_FILTERS:
      return { ...state, searchFilters: {} };
    
    case ACTIONS.UPDATE_PREFERENCES:
      return {
        ...state,
        preferences: { ...state.preferences, ...action.payload }
      };
    
    default:
      return state;
  }
};

// Store context
const StoreContext = createContext();

// Store provider
export const StoreProvider = ({ children }) => {
  const [state, dispatch] = useReducer(reducer, initialState);
  
  return (
    <StoreContext.Provider value={{ state, dispatch }}>
      {children}
    </StoreContext.Provider>
  );
};

// Hook to use the store
export const useStore = () => {
  const context = useContext(StoreContext);
  
  if (!context) {
    throw new Error('useStore must be used within a StoreProvider');
  }
  
  return context;
};