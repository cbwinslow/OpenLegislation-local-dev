# JAXB/USLM Schema Setup for Federal Data Integration

## Overview
To add full schema support for USLM (United States Legislative Markup) from the usgpo/uslm GitHub repo, download the XSD schemas and generate JAXB classes. This replaces basic DOM parsing in the federal processors with strongly-typed JAXB objects for better validation and mapping.

## Step-by-Step Setup

### 1. Create the Schema Folder
- In VS Code or terminal, create the directory if it doesn't exist:
  ```
  mkdir -p src/main/resources/schema
  ```
- This folder stores XSD files (e.g., uslm-bill.xsd). It can hold multiple schemas for different collections (bills, laws, etc.).

### 2. Download the USLM XSD Schema
- The main schema for bills is `uslm-bill.xsd` from usgpo/uslm.
- Run this in terminal to download it to the folder:
  ```
  curl -o src/main/resources/schema/uslm-bill.xsd https://raw.githubusercontent.com/usgpo/uslm/main/uslm-bill.xsd
  ```
- Verify: `ls src/main/resources/schema/` should show `uslm-bill.xsd`.
- For other collections (e.g., laws), download additional XSDs to the same folder (e.g., `uslm-law.xsd`).

### 3. Add JAXB Generation Plugin to pom.xml
- Edit `pom.xml` under `<build><plugins>` to include the `jaxb2-maven-plugin` for generating Java classes during `mvn generate-sources`.
- Add this plugin:
  ```
  <plugin>
    <groupId>org.codehaus.mojo</groupId>
    <artifactId>jaxb2-maven-plugin</artifactId>
    <version>2.6.6</version>
    <executions>
      <execution>
        <id>xjc</id>
        <goals>
          <goal>xjc</goal>
        </goals>
        <configuration>
          <sources>
            <source>src/main/resources/schema/uslm-bill.xsd</source>
          </sources>
          <packageName>gov.nysenate.openleg.processors.federal.jaxb</packageName>
          <clearOutputDir>false</clearOutputDir>
          <outputDirectory>target/generated-sources/xjc</outputDirectory>
          <generateEpisode>false</generateEpisode>
        </configuration>
      </execution>
    </executions>
    <dependencies>
      <dependency>
        <groupId>com.sun.xml.bind</groupId>
        <artifactId>jaxb-xjc</artifactId>
        <version>2.3.1</version>
      </dependency>
    </dependencies>
  </plugin>
  ```
- This generates classes in `target/generated-sources/xjc/gov/nysenate/openleg/processors/federal/jaxb/` (e.g., `BillJaxb.java`, `LegislationIdJaxb.java`).

### 4. Add JAXB Runtime Dependencies to pom.xml
- Under `<dependencies>`, add runtime for JAXB (required for unmarshaling):
  ```
  <dependency>
    <groupId>com.sun.xml.bind</groupId>
    <artifactId>jaxb-impl</artifactId>
    <version>2.3.1</version>
  </dependency>
  <dependency>
    <groupId>jakarta.xml.bind</groupId>
    <artifactId>jakarta.xml.bind-api</artifactId>
    <version>3.0.1</version>
  </dependency>
  ```

### 5. Generate the JAXB Classes
- Run Maven to generate:
  ```
  mvn clean generate-sources
  ```
- Output: Check `target/generated-sources/xjc/` for generated classes (e.g., `BillType.java`, `LegislationId.java`, `Sponsor.java`). These represent USLM elements like `<bill>`, `<legislation-id>`, `<sponsor>`, `<action>`, `<text>`.

### 6. Update Processor to Use JAXB
- In `FederalBillXmlProcessor.java`, replace DOM parsing with JAXB:
  ```java
  private Bill mapToBill(File xmlFile, FederalBillXmlFile sourceFile) throws Exception {
    JAXBContext jaxbContext = JAXBContext.newInstance(ObjectFactory.class); // From generated
    Unmarshaller unmarshaller = jaxbContext.createUnmarshaller();
    BillJaxb billJaxb = unmarshaller.unmarshal(xmlFile); // Unmarshal to generated BillJaxb
    // Map: billJaxb.getLegislationId().getCongress() → congress
    // billJaxb.getOfficialTitle() → Bill.setTitle(title)
    // billJaxb.getSponsor().getFullName() → BillSponsor
    // etc.
    return mapJaxbToBill(billJaxb, sourceFile);
  }
  ```
- Implement `mapJaxbToBill()` using generated getters (e.g., `billJaxb.getLegislationId().getCongress()`).
- Run `mvn clean compile` to verify.

### 7. For Multiple Schemas (e.g., Laws)
- Add more `<source>` in plugin config:
  ```
  <sources>
    <source>src/main/resources/schema/uslm-bill.xsd</source>
    <source>src/main/resources/schema/uslm-law.xsd</source>
  </sources>
  ```
- Generate for all, or separate executions.

### Troubleshooting
- **XSD Validation Errors**: If XSD has includes, download all related XSDs to the folder.
- **Generation Fails**: Ensure XSD URL is correct; check logs for schema issues.
- **Runtime Errors**: Add `@XmlRootElement` if needed in generated classes.
- **Multi-Schema**: Use separate plugin executions for different packages (bills vs. laws).

After setup, update processors (e.g., `FederalLawXmlProcessor`) similarly. Run `mvn clean test` to verify generated classes compile.
