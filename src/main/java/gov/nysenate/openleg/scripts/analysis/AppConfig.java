package gov.nysenate.openleg.scripts.analysis;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.PropertySource;

@Configuration
@ComponentScan(basePackages = "gov.nysenate.openleg")
@PropertySource("classpath:application.properties")
public class AppConfig {}
