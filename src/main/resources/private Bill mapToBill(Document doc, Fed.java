private Bill mapToBill(Document doc, FederalBillXmlFile sourceFile) {
    Element billElem = (Element) doc.getElementsByTagName("bill").item(0);

    // BaseBillId
    Element legIdElem = (Element) billElem.getElementsByTagName("legislation-id").item(0);
    int congress = Integer.parseInt(legIdElem.getElementsByTagName("congress").item(0).getTextContent());
    String type = legIdElem.getElementsByTagName("type").item(0).getTextContent();
    String number = legIdElem.getElementsByTagName("number").item(0).getTextContent();
    Chamber chamber = type.startsWith("H") ? Chamber.HOUSE : Chamber.SENATE;
    BillType billType = BillType.fromString(type.toUpperCase()); // Assume fromString exists
    int sessionYear = congressToSessionYear(congress);
    BaseBillId baseBillId = new BaseBillId(number, sessionYear, billType);

    Bill bill = new Bill(baseBillId);
    bill.setTitle(billElem.getElementsByTagName("official-title").item(0).getTextContent());

    // Sponsors
    NodeList sponsorNodes = billElem.getElementsByTagName("sponsor");
    for (int i = 0; i < sponsorNodes.getLength(); i++) {
        Element sponsorElem = (Element) sponsorNodes.item(i);
        String name = sponsorElem.getElementsByTagName("full-name").item(0).getTextContent();
        String state = sponsorElem.getElementsByTagName("state").item(0).getTextContent();
        String party = sponsorElem.getElementsByTagName("party").item(0).getTextContent();
        BillSponsor sponsor = new BillSponsor(name, null, party, state, chamber, true);
        bill.addSponsor(sponsor);
    }

    // Actions
    NodeList actionNodes = billElem.getElementsByTagName("action");
    for (int i = 0; i < actionNodes.getLength(); i++) {
        Element actionElem = (Element) actionNodes.item(i);
        LocalDate date = LocalDate.parse(actionElem.getElementsByTagName("date").item(0).getTextContent(), DATE_FORMAT);
        String chamberStr = actionElem.getElementsByTagName("chamber").item(0).getTextContent();
        Chamber actionChamber = "HOUSE".equals(chamberStr) ? Chamber.HOUSE : Chamber.SENATE;
        String text = actionElem.getElementsByTagName("text").item(0).getTextContent();
        BillAction action = new BillAction(date.atStartOfDay(), actionChamber, text, BillActionType.UNKNOWN);
        bill.addAction(action);
    }

    // Text
    BillText billText = new BillText();
    NodeList sectionNodes = billElem.getElementsByTagName("section");
    StringBuilder textBuilder = new StringBuilder();
    for (int i = 0; i < sectionNodes.getLength(); i++) {
        Element sectionElem = (Element) sectionNodes.item(i);
        String heading = sectionElem.getElementsByTagName("heading").item(0).getTextContent();
        String content = sectionElem.getElementsByTagName("content").item(0).getTextContent();
        textBuilder.append(heading).append(": ").append(content).append("\n");
    }
    billText.setText(BillTextFormat.PLAIN, textBuilder.toString());
    bill.setText(billText);

    bill.setPublishDateTime(sourceFile.getPublishedDateTime());
    return bill;
}