package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalMember;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public class FederalMemberDao {
    // Mock for simulation; in real, use JPA or JDBC to query/upsert
    public List<FederalMember> findByCongress(int congress) {
        // Simulate fetching from API or DB
        FederalMember member = new FederalMember();
        member.setBioguideId("mock-" + congress);
        member.setFullName("Mock Member " + congress);
        return List.of(member);  // 1 per congress for demo; real would fetch real data
    }
}
