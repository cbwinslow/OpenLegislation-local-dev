package gov.nysenate.openleg.dao.federal;

import gov.nysenate.openleg.model.federal.FederalRegister;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;

/**
 * Data access layer for federal register operations.
 */
@Repository
public interface FederalRegisterDao extends JpaRepository<FederalRegister, Long> {

    /**
     * Find a federal register document by its document number.
     */
    List<FederalRegister> findByDocumentNumber(String documentNumber);

    /**
     * Find federal register documents by publication date.
     */
    List<FederalRegister> findByPublicationDateOrderByTitleAsc(LocalDate publicationDate);

    /**
     * Find federal register documents by agency.
     */
    List<FederalRegister> findByAgencyOrderByPublicationDateDesc(String agency);

    /**
     * Find federal register documents by document type.
     */
    List<FederalRegister> findByDocumentTypeOrderByPublicationDateDesc(String documentType);

    /**
     * Find federal register documents by date range.
     */
    @Query("SELECT fr FROM FederalRegister fr WHERE fr.publicationDate BETWEEN :startDate AND :endDate " +
           "ORDER BY fr.publicationDate DESC")
    List<FederalRegister> findByPublicationDateBetween(
        @Param("startDate") LocalDate startDate,
        @Param("endDate") LocalDate endDate
    );

    /**
     * Search federal register documents by title (case-insensitive partial match).
     */
    @Query("SELECT fr FROM FederalRegister fr WHERE " +
           "LOWER(fr.title) LIKE LOWER(CONCAT('%', :title, '%')) " +
           "ORDER BY fr.publicationDate DESC")
    List<FederalRegister> searchByTitle(@Param("title") String title);

    /**
     * Get count of documents by agency.
     */
    @Query("SELECT COUNT(fr) FROM FederalRegister fr WHERE fr.agency = :agency")
    long countByAgency(@Param("agency") String agency);

    /**
     * Get count of documents by document type.
     */
    @Query("SELECT COUNT(fr) FROM FederalRegister fr WHERE fr.documentType = :documentType")
    long countByDocumentType(@Param("documentType") String documentType);
}