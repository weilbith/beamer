<template>
  <input id="imprint-modal" type="checkbox" class="modal-toggle" />
  <div class="modal">
    <div class="modal-box bg-dark w-8/12 max-w-5xl p-14">
      <h2 class="font-bold">Impressum</h2>
      <div class="py-4">
        <div>
          <h3>Angaben gemäß § 5 TMG</h3>
          <p>
            brainbot technologies AG<br />
            Taunusstr. 61<br />
            55120 Mainz
          </p>
          <h3>Vertreten durch</h3>
          <p>Herr Heiko Hees</p>
          <h3>Kontakt</h3>
          <p>
            Telefon: +49 (0) 6131 2116391 Telefax: +49 (0) 6131 2116392 E-Mail:
            contact[at]brainbot.com
          </p>
          <h3>Registereintrag</h3>
          <p>
            Eintragung im Handelsregister. Registergericht: Amtsgericht Mainz Registernummer: 8375
            Mainz
          </p>
          <h3>Umsatzsteuer-Identifikationsnummer</h3>
          <p>gemäß §27 a Umsatzsteuergesetz: DE231725642</p>
          <h3>Aufsichtsbehörde</h3>
          <p>Landratsamt Mainz</p>
          <h3>Inhaltlich Verantwortlicher</h3>
          <p>gemäß § 6 MDStV: Heiko Hees</p>
          <h3>Haftungsausschluss:</h3>
          <h3>Haftung für Inhalte</h3>
          <p>
            Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit,
            Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen.
            Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten
            nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als
            Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde
            Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige
            Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung der Nutzung von
            Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine
            diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten
            Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen
            werden wir diese Inhalte umgehend entfernen.
          </p>
          <h3>Haftung für Links</h3>
          <p>
            Unser Angebot enthält Links zu externen Webseiten Dritter, auf deren Inhalte wir keinen
            Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr
            übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder
            Betreiber der Seiten verantwortlich. Die verlinkten Seiten wurden zum Zeitpunkt der
            Verlinkung auf mögliche Rechtsverstöße überprüft. Rechtswidrige Inhalte waren zum
            Zeitpunkt der Verlinkung nicht erkennbar. Eine permanente inhaltliche Kontrolle der
            verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer Rechtsverletzung nicht
            zumutbar. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Links umgehend
            entfernen.
          </p>
          <h3>Urheberrecht</h3>
          <p>
            Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten
            unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung
            und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der
            schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien
            dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. Soweit
            die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die
            Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche
            gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam
            werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von
            Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.
          </p>
          <h3>Datenschutz</h3>
          <p>
            Die Nutzung unserer Webseite ist in der Regel ohne Angabe personenbezogener Daten
            möglich. Soweit auf unseren Seiten personenbezogene Daten (beispielsweise Name,
            Anschrift oder eMail-Adressen) erhoben werden, erfolgt dies, soweit möglich, stets auf
            freiwilliger Basis. Diese Daten werden ohne Ihre ausdrückliche Zustimmung nicht an
            Dritte weitergegeben. Wir weisen darauf hin, dass die Datenübertragung im Internet
            (z.B. bei der Kommunikation per E-Mail) Sicherheitslücken aufweisen kann. Ein
            lückenloser Schutz der Daten vor dem Zugriff durch Dritte ist nicht möglich. Der
            Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten durch Dritte
            zur Übersendung von nicht ausdrücklich angeforderter Werbung und
            Informationsmaterialien wird hiermit ausdrücklich widersprochen. Die Betreiber der
            Seiten behalten sich ausdrücklich rechtliche Schritte im Falle der unverlangten
            Zusendung von Werbeinformationen, etwa durch Spam-Mails, vor.
          </p>
        </div>
      </div>
      <div class="modal-action">
        <label for="imprint-modal" class="btn hover:bg-teal-light-35">OK</label>
      </div>
    </div>
  </div>
</template>
<style lang="css">
.modal-box::-webkit-scrollbar {
  width: 6px;
}
.modal-box::-webkit-scrollbar-track {
  @apply bg-teal my-4;
}

.modal-box::-webkit-scrollbar-thumb {
  @apply bg-teal-light-35;
}

.modal-box h2 {
	@apply text-2xl font-bold py-6;
}

.modal-box h3 {
	@apply text-xl font-bold pb-2;
}

.modal-box p {
	@apply pb-10;
}
</style>
