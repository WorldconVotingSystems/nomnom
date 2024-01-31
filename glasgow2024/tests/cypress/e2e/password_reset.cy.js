// The user data
import user from '../fixtures/users.json'

describe('template spec', () => {
  it('passes', () => {
    // cy.wrap(users).each(
    for (let i = 25; i <= 100; i++) {       
      // Make sure that there are no sessions
      cy.clearAllCookies()
      // Go to the nominations site
      cy.visit('https://registration.glasgow2024.org/login')

      // Click the login with Clyde button - long selector because no id etc
      cy.get('.forgotpassword').first().click()

      let email = `${user.email_name}${String(i).padStart(3, '0')}@${user.email_domain}`
      // On Clyde login with the user email and password
      cy.get('#reset > form').within(
        ($form) => {
          cy.get('input[name="email"]').type(email)
          cy.root().submit()
        }
      )
    }
  })
})

