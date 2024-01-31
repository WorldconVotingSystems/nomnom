// The user data
import user from '../fixtures/users.json'

// Run using npm run cypress:open -- --env CLYDE_PASSWORD=xxxxxxx
describe('template spec', () => {
  it('has variables CLYDE_PASSWORD', () => {
    expect(Cypress.env('CLYDE_PASSWORD')).to.not.be.undefined
  })

  it('passes', () => {

    let password = Cypress.env('CLYDE_PASSWORD')

    // cy.wrap(users).each(
    for (let i = 1; i <= 100; i++) {       
      // Make sure that there are no sessions
      cy.clearAllCookies()
      // Go to the nominations site
      cy.visit('https://nominations.glasgow2024.org')

      // Click the login with Clyde button - long selector because no id etc
      cy.get('main.main-block.flex-shrink-0 div.container-fluid div.flex-row div.d-flex.justify-content-center.align-items-center.bd-highlight div.d-flex div.p-5.text-center.bg-body-tertiary div.container.py-5 div.d-inline-flex.gap-2.mb-5 a button.d-inline-flex.align-items-center.btn.btn-primary.btn-lg.px-4.rounded-pill').click()

      let email = `${user.email_name}${String(i).padStart(3, '0')}@${user.email_domain}`
      // On Clyde login with the user email and password
      cy.get('#login > form').within(
        ($form) => {
          cy.get('input[name="username"]').type(email)
          cy.get('input[name="password"]').type(password)
          cy.root().submit()
        }
      )

      // Select the registrant to auth as for NomNom
      cy.get('.product-card').get('.text-muted').should('contain', email)
      cy.get('.product-card').get('form').within(
        ($form) => {
          cy.root().submit()
        }
      )

      // Test logout contains expected name
      cy.get('#navbarContent > .navbar-nav > .nav-item > form > .btn').should('contain', `${user.name} ${String(i).padStart(3, '0')}`)
    }
  })
})

