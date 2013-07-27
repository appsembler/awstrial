#!/bin/perl

################################################################################
# css_search.pl                                                                #
################################################################################
#                                                                              #
# This quick and dirty script lets you see which CSS files contain the         #
# definition for the ID and Class attributes you are using.                    #
#                                                                              #
# Usage:                                                                       #
#     ./css_search.pl source_html css_file1 [css_file2 [css_fileN]]            #
#                                                                              #
# Output:                                                                      #
#     $selector found in $css_file - For the first file containing $selector   #
#     Selectors not found: - All remaining selectors used in source_html       #
#                                                                              #
################################################################################

my $sourcefile = shift @ARGV;
my @deffiles = @ARGV;
my %css = ();

open(S, "<$sourcefile") || die "Could not open $sourcefile\n$!";
my $ln = 1;

my $regex = qr/(class|id)=\"([^\"]+)\"/;
while (my $line = <S>) {
    while ($line =~ m/$regex/g) {
        for my $def (split(/\s+/, $2)) {
            if ($1 eq "class") { $def = ".$def"; } else { $def = "#$def"; }
            $css{$def} = 1;
        }
    }
}

$/ = undef;
for my $cssfile (@deffiles) {
    open(F, "<$cssfile") || die "Could not open $cssfile\n$!";
    my $csscontent = <F>;
    close(F);
    for my $selector (keys %css) {
        if ($csscontent =~ /$selector/)  {
            print "$selector found in $cssfile\n";
            delete $css{$selector};
        }
    }
}

print "Selectors not found:\n";
for my $unknown (keys %css) {
    print $unknown, "\n";
}

