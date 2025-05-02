/// <reference types="cypress" />

describe('Authentication Flow', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    cy.clearLocalStorage();
  });

  it('should redirect to login when accessing protected route without auth', () => {
    cy.visit('/app');
    cy.url().should('include', '/login');
  });

  it('should show login form with all elements', () => {
    cy.visit('/login');
    
    // Check form elements
    cy.get('h2').should('contain.text', 'Sign in to your account');
    cy.get('input[name="username"]').should('be.visible');
    cy.get('input[name="password"]').should('be.visible');
    cy.get('input[name="remember"]').should('be.visible');
    cy.contains('button', 'Sign in').should('be.visible');
    
    // Check links
    cy.contains('a', 'create a new account').should('have.attr', 'href', '/register');
    cy.contains('a', 'Forgot your password').should('have.attr', 'href', '/forgot-password');
  });

  it('should validate required fields on login', () => {
    cy.visit('/login');
    
    // Submit without filling fields
    cy.contains('button', 'Sign in').click();
    
    // Check validation errors
    cy.contains('Username is required').should('be.visible');
  });

  it('should display error on invalid credentials', () => {
    cy.visit('/login');
    
    // Fill form with invalid credentials
    cy.get('input[name="username"]').type('wronguser');
    cy.get('input[name="password"]').type('wrongpass');
    
    // Intercept API call to mock error response
    cy.intercept('POST', '**/auth/login', {
      statusCode: 401,
      body: {
        detail: 'Invalid username or password'
      }
    }).as('loginRequest');
    
    // Submit form
    cy.contains('button', 'Sign in').click();
    
    // Verify API was called
    cy.wait('@loginRequest');
    
    // Check error message
    cy.contains('Invalid username or password').should('be.visible');
  });

  it('should login with valid credentials and redirect to dashboard', () => {
    cy.visit('/login');
    
    // Fill form with valid credentials
    cy.get('input[name="username"]').type('testuser');
    cy.get('input[name="password"]').type('testpassword');
    
    // Intercept API call to mock success response
    cy.intercept('POST', '**/auth/login', {
      statusCode: 200,
      body: {
        access_token: 'fake-access-token',
        refresh_token: 'fake-refresh-token',
        token_type: 'bearer'
      }
    }).as('loginRequest');
    
    // Intercept user profile API call
    cy.intercept('GET', '**/users/me', {
      statusCode: 200,
      body: {
        id: '123',
        username: 'testuser',
        email: 'test@example.com',
        full_name: 'Test User',
        is_admin: false
      }
    }).as('getUserProfile');
    
    // Submit form
    cy.contains('button', 'Sign in').click();
    
    // Verify API was called
    cy.wait('@loginRequest');
    cy.wait('@getUserProfile');
    
    // Verify redirect to dashboard
    cy.url().should('include', '/app');
    
    // Verify localStorage has tokens
    cy.window().then((window) => {
      expect(window.localStorage.getItem('access_token')).to.equal('fake-access-token');
      expect(window.localStorage.getItem('refresh_token')).to.equal('fake-refresh-token');
    });
  });

  it('should register a new account', () => {
    cy.visit('/register');
    
    // Fill registration form
    cy.get('input[name="username"]').type('newuser');
    cy.get('input[name="email"]').type('newuser@example.com');
    cy.get('input[name="password"]').type('Password123!');
    cy.get('input[name="confirmPassword"]').type('Password123!');
    cy.get('input[name="full_name"]').type('New User');
    
    // Intercept API call to mock success response
    cy.intercept('POST', '**/auth/register', {
      statusCode: 201,
      body: {
        id: '456',
        username: 'newuser',
        email: 'newuser@example.com',
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token'
      }
    }).as('registerRequest');
    
    // Intercept user profile API call
    cy.intercept('GET', '**/users/me', {
      statusCode: 200,
      body: {
        id: '456',
        username: 'newuser',
        email: 'newuser@example.com',
        full_name: 'New User',
        is_admin: false
      }
    }).as('getUserProfile');
    
    // Submit form
    cy.contains('button', 'Create Account').click();
    
    // Verify API was called
    cy.wait('@registerRequest');
    cy.wait('@getUserProfile');
    
    // Verify redirect to dashboard
    cy.url().should('include', '/app');
  });

  it('should logout and redirect to login page', () => {
    // Set up fake authentication first
    cy.window().then((window) => {
      window.localStorage.setItem('access_token', 'fake-token');
      window.localStorage.setItem('refresh_token', 'fake-refresh-token');
    });
    
    // Mock user profile to pass authentication
    cy.intercept('GET', '**/users/me', {
      statusCode: 200,
      body: {
        id: '123',
        username: 'testuser',
        email: 'test@example.com'
      }
    }).as('getUserProfile');
    
    // Visit dashboard
    cy.visit('/app');
    cy.wait('@getUserProfile');
    
    // Intercept logout API call
    cy.intercept('POST', '**/auth/logout', {
      statusCode: 200,
      body: { message: 'Logged out successfully' }
    }).as('logoutRequest');
    
    // Click profile dropdown
    cy.get('[aria-label="Open user menu"]').click();
    
    // Click logout button
    cy.contains('Sign out').click();
    
    // Verify API was called
    cy.wait('@logoutRequest');
    
    // Verify redirect to login
    cy.url().should('include', '/login');
    
    // Verify localStorage tokens are removed
    cy.window().then((window) => {
      expect(window.localStorage.getItem('access_token')).to.be.null;
      expect(window.localStorage.getItem('refresh_token')).to.be.null;
    });
  });
});